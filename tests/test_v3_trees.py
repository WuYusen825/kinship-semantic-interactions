import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis/v3'))
from tree_feasibility import parse_newick,walk
class TreeTest(unittest.TestCase):
    def test_nested_tree_preserves_internal_language(self):
        root=parse_newick('((a:1,b:2)c:3,d:4)family:1;')
        nodes={n.name:n for n in walk(root)}
        self.assertEqual(set(nodes),{'a','b','c','d','family'})
        self.assertEqual(nodes['c'].length,3)
        self.assertEqual(len(nodes['c'].children),2)
    def test_rejects_unbalanced(self):
        with self.assertRaises((ValueError,IndexError)):parse_newick('(a:1,b:1;')
    def test_topology_without_lengths(self):
        self.assertTrue(all(n.length is None for n in walk(parse_newick('(a,b)root;'))))
if __name__=='__main__':unittest.main()
