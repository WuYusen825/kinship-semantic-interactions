"""S2二项工作似然、MLE与预置Firth替代；只使用调用者传入的数据。"""
import numpy as np
from scipy.optimize import linprog
from scipy.special import expit, logit
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
import warnings
from design_rank import abstract_rows, M4_COLUMNS

MODELS=('M0','M1','M2','M3','M4')
COMPARISONS=(('M0','M1'),('M0','M2'),('M1','M2'),('M0','M4'),('M2','M4'),('M2','M3'),('M4','M3'))

def build_design(pair_types, model):
    rows={r['category_a']+'|'+r['category_b']:r for r in abstract_rows()}
    if model=='M3':
        return np.eye(len(pair_types))
    columns={'M0':M4_COLUMNS[:4],'M1':M4_COLUMNS[:4]+('Dq',),
             'M2':M4_COLUMNS[:7],'M4':M4_COLUMNS}[model]
    for r in rows.values():r['Dq']=int(r['Dr']!=r['De'])
    return np.array([[rows[k][c] for c in columns] for k in pair_types],dtype=float)

def check_separation(X, success, total):
    if np.all((success>0)&(success<total)):
        return False,0.0
    A=np.concatenate([X[success>0],-X[success<total]],axis=0)
    result=linprog(-A.sum(axis=0),A_ub=-A,b_ub=np.zeros(len(A)),
                   bounds=[(-1,1)]*X.shape[1],method='highs')
    if not result.success:raise RuntimeError('分离线性规划失败：'+result.message)
    objective=float(-result.fun)
    return objective>1e-8,objective

def _ll(X,s,t,b):
    eta=X@b
    return float(s@eta-t@np.logaddexp(0,eta))

def _information(X,t,b):
    p=expit(X@b)
    return p,X.T@((t*p*(1-p))[:,None]*X)

def fit_aggregated(X, success, total, estimator='MLE'):
    """28行加权成功数/总量；返回含截距的beta及可审计诊断。

    M3以28列完整独热编码无额外截距。MLE先查分离，按协议转Firth。
    非整数权重下是工作似然的Firth型校正，不声称独立整数样本偏差性质。
    """
    if estimator!='MLE':raise ValueError('聚合API仅用于MLE及其Firth替代；C1调用逐行参照接口。')
    X=np.asarray(X,float);s=np.asarray(success,float);t=np.asarray(total,float)
    keep=t>0;X=X[keep];s=s[keep];t=t[keep]
    rank=int(np.linalg.matrix_rank(X));size=X.shape[1]
    if rank<size:raise ValueError(f'训练设计不满秩 {rank}/{size}')
    if np.any(s< -1e-10) or np.any(s>t+1e-10):raise ValueError('二项聚合计数越界')
    s=np.clip(s,0,t);weight_sum=float(t.sum())
    separated,margin=check_separation(X,s,t)
    diag={'rank':rank,'weight_sum':weight_sum,'separation':bool(separated),
          'separation_lp_objective':margin,'method':'MLE','converged':False}
    b=np.zeros(size);iterations=0;failure=None
    if not separated:
        for iterations in range(1,5001):
            p,H=_information(X,t,b);score=X.T@(s-t*p)
            norm=float(np.max(np.abs(score))/weight_sum)
            if norm<=1e-8:
                diag.update(converged=True,iterations=iterations,standardized_score=norm)
                break
            try:step=np.linalg.solve(H,score)
            except np.linalg.LinAlgError:
                failure='MLE信息矩阵数值奇异';break
            old=_ll(X,s,t,b);scale=1.0
            for _ in range(60):
                candidate=b+scale*step
                value=_ll(X,s,t,candidate)
                if np.isfinite(value) and value>=old-1e-12:
                    b=candidate;break
                scale*=0.5
            else:failure='MLE线搜索失败';break
        if diag['converged'] and np.isfinite(b).all():
            diag.update(max_abs_beta=float(np.abs(b).max()),min_probability=float(expit(X@b).min()),max_probability=float(expit(X@b).max()))
            return b,diag
        failure=failure or 'MLE得分或迭代阈值未通过'
    else:failure='检出完全或准完全分离'
    # 预先固定的Firth型Jeffreys工作似然校正；不得临时换ridge。
    diag.update(method='Firth',trigger=failure);b=np.zeros(size)
    def adjusted(beta):
        p,I=_information(X,t,beta)
        sign,ld=np.linalg.slogdet(I)
        if sign<=0:return -np.inf,None,None
        inv=np.linalg.inv(I)
        h=t*p*(1-p)*np.einsum('ij,jk,ik->i',X,inv,X)
        score=X.T@(s-t*p+h*(0.5-p))
        return _ll(X,s,t,beta)+0.5*ld,score,I
    for iterations in range(1,10001):
        old,score,I=adjusted(b)
        if score is None:break
        norm=float(np.max(np.abs(score))/weight_sum)
        if norm<=1e-8:
            diag.update(converged=True,iterations=iterations,standardized_score=norm)
            break
        step=np.linalg.solve(I,score);scale=1.0
        for _ in range(40):
            candidate=b+scale*step;value,_,_=adjusted(candidate)
            if np.isfinite(value) and value>=old-1e-12:
                b=candidate;break
            scale*=0.5
        else:break
    if not diag['converged']:
        _,score,_=adjusted(b)
        diag.update(iterations=iterations,standardized_score=float(np.max(np.abs(score))/weight_sum) if score is not None else None)
    diag.update(max_abs_beta=float(np.abs(b).max()),min_probability=float(expit(X@b).min()),max_probability=float(expit(X@b).max()))
    return b,diag

def fit_c1_rows(X,y,weights,model):
    """精确保持冻结/S1的C=1逐行参数化和数值设定。"""
    features=X if model=='M3' else X[:,1:]
    est=LogisticRegression(C=1,l1_ratio=0,solver='lbfgs',tol=1e-9,max_iter=5000)
    with warnings.catch_warnings(record=True) as messages:
        warnings.simplefilter('always');est.fit(features,y,sample_weight=weights)
    beta=est.coef_[0]+est.intercept_[0] if model=='M3' else np.r_[est.intercept_[0],est.coef_[0]]
    diag={'method':'C1','converged':not any(issubclass(w.category,ConvergenceWarning) for w in messages),
          'iterations':int(est.n_iter_[0]),'rank':int(np.linalg.matrix_rank(X)),
          'weight_sum':float(weights.sum()),'warnings':[str(w.message) for w in messages]}
    return beta,diag

def logloss(y,p):
    p=np.clip(p,1e-15,1-1e-15)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))
