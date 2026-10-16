"""用保存的S2结果生成中文研究图；不重估模型。"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.ticker import PercentFormatter
import numpy as np

HERE=Path(__file__).resolve().parent
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(FONT)
plt.rcParams.update({'font.family':fm.FontProperties(fname=FONT).get_name(),'axes.unicode_minus':False,
                     'font.size':16,'axes.spines.top':False,'axes.spines.right':False,
                     'savefig.facecolor':'white'})
COLORS={'M0':'#888888','M1':'#bf682e','M2':'#1d597f'}
AREA={'全部':'全样本','Africa':'非洲','Australia':'澳大利亚','Eurasia':'欧亚大陆',
      'North America':'北美洲','Papunesia':'巴布亚—太平洋','South America':'南美洲'}

def main():
    pred=json.loads((HERE/'prediction_results.json').read_text())
    part=json.loads((HERE/'partition_results.json').read_text())
    cells=pred['full_sample_calibration']['D1_MLE_family']
    panels=['全部','Africa','Australia','Eurasia','North America','Papunesia','South America']
    fig,axes=plt.subplots(3,3,figsize=(11.5,8.7),sharey=True,sharex=True)
    figure_data={'seven_cells':cells,'directions':{},'multiverse':[]}
    for ax,area in zip(axes.flat,panels):
        rows=[r for r in cells if r['area']==area]
        patterns=sorted({r['pattern'] for r in rows});x=np.arange(len(patterns))
        for m in ['M0','M1','M2']:
            lookup={r['pattern']:r for r in rows if r['model']==m}
            ax.plot(x,[lookup[p]['predicted'] for p in patterns],color=COLORS[m],lw=1.5,
                    linestyle={'M0':':','M1':'--','M2':'-'}[m],label=m+'：全样本MLE拟合')
        lookup={r['pattern']:r for r in rows if r['model']=='M2'}
        ax.scatter(x,[lookup[p]['observed'] for p in patterns],s=29,color='#111111',zorder=5,label='区域实测比例')
        ax.set_title(AREA[area]);ax.set_xticks(x,patterns,rotation=0,fontsize=14);ax.set_ylim(-.025,1.025)
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='y',alpha=.16)
    axes[0,0].set_ylabel('共用词形比例');axes[1,0].set_ylabel('共用词形比例');axes[2,0].set_ylabel('共用词形比例')
    axes.flat[-2].axis('off');axes.flat[-1].axis('off')
    axes.flat[-2].text(0,.6,'点：区域内谱系等权比例\n线：全样本无惩罚拟合\n所有分面重复同一组拟合线',fontsize=14,va='center')
    handles,labels=axes[0,0].get_legend_handles_labels()
    axes.flat[-1].legend(handles,labels,loc='center left',frameon=False,fontsize=14)
    fig.supxlabel('差异单元：所指者性别、年龄、参照者性别差异（依次编码）',y=.04)
    fig.text(.02,.005,'区域实测按区域内谱系等权；所有面板重复同一全样本拟合线。全样本含地域缺失记录，六区分面仅含地域已知记录。',fontsize=12)
    fig.tight_layout(rect=(0,.065,1,1));fig.savefig(HERE/'s2_seven_cells.png',dpi=240);fig.savefig(HERE/'s2_seven_cells.svg');plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(10.2,4.2),sharey=True)
    labels=['P2：性别区分偏年长侧','P3：年龄区分偏男性侧','P4：年龄区分偏同性侧']
    for j,(unit,title) in enumerate([('systems','系统计数'),('families','谱系组多数方向计数')]):
        ax=axes[j]
        for i,h in enumerate(['P2','P3','P4']):
            v=part['P2_P4'][h]['strict_direction']['overall'];figure_data['directions'][h]=v
            positive=v['systems_predicted'] if unit=='systems' else v['families_predicted_majority']
            negative=v['systems_opposite'] if unit=='systems' else v['families_opposite_majority']
            ax.scatter(positive,i-.11,s=55,color='#1d597f',label='符合预测侧' if i==0 else None)
            ax.scatter(negative,i+.11,s=55,marker='D',color='#bf682e',label='相反侧' if i==0 else None)
            ax.annotate(str(positive),(positive,i-.11),xytext=(6,0),textcoords='offset points',va='center')
            ax.annotate(str(negative),(negative,i+.11),xytext=(6,0),textcoords='offset points',va='center')
        ax.set_title(title)
        if j==0:ax.set_yticks(range(3),labels)
        ax.grid(axis='x',alpha=.16)
        ax.set_xlim(left=0,right=92 if unit=='systems' else 25);ax.set_xlabel('计数')
    axes[0].invert_yaxis()
    handles,labels=axes[1].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.65,.075),ncol=2,frameon=False,fontsize=14)
    fig.text(.03,.015,'谱系内按有关系统的多数方向计数；P3的一个平局谱系另列，不进入方向检验。',fontsize=12)
    fig.tight_layout(rect=(0,.19,1,1));fig.savefig(HERE/'s2_hierarchy_directions.png',dpi=240);fig.savefig(HERE/'s2_hierarchy_directions.svg');plt.close(fig)

    fig,axes=plt.subplots(1,3,figsize=(15.7,10.3),sharey=True)
    rows=[(d,e,w) for d in ['D1','D2','D3','D4','D5'] for e in ['MLE','C1'] for w in ['family','language']]
    texts=[f'{d}  '+('无惩罚' if e=='MLE' else 'C=1')+'  '+('谱系等权' if w=='family' else '语言等权') for d,e,w in rows]
    for ax,cv,title in zip(axes,['family','area','language'],['留出谱系','留出宏观区域','留出语言（参照）']):
        for i,(d,e,w) in enumerate(rows):
            for comparison,offset,color in [('M0-M4',-.13,'#1d597f'),('M2-M4',.13,'#bf682e')]:
                key=f'{d}_{e}_{w}_{cv}';v=pred['settings'][key]['comparisons'][comparison]
                lo,hi=v['family_cluster_bootstrap_95ci'];point=v['gain']
                ax.plot([lo,hi],[i+offset]*2,color=color,lw=1.1)
                ax.scatter(point,i+offset,s=17,color=color,label=comparison if i==0 else None,zorder=3)
                figure_data['multiverse'].append({'setting':key,'comparison':comparison,**v})
        ax.axvline(0,color='#555555',lw=.9);ax.set_title(title);ax.grid(axis='y',alpha=.12)
        ax.set_yticks(range(20),texts);ax.set_xlabel('对数损失增益（正值利于M4）')
    axes[0].invert_yaxis();axes[-1].legend(loc='lower right',frameon=False)
    fig.suptitle('全部交叉设定：点估计与固定折外预测的谱系整组自助95%区间',y=.995)
    fig.tight_layout(rect=(0,0,1,.975));fig.savefig(HERE/'s2_multiverse_forest.png',dpi=220);fig.savefig(HERE/'s2_multiverse_forest.svg');plt.close(fig)
    (HERE/'s2_figure_data.json').write_text(json.dumps(figure_data,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
