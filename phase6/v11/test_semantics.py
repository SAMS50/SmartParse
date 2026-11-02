import unittest
from .semantics import Validator, projection, compare


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.v=Validator()
        if not self.v.compiler:self.skipTest('Clang unavailable')

    def p(self,s):return projection(s,self.v.inspect(s))

    def test_ownership_scope_binding(self):
        a=self.p('int f(int x){int y=0;if(x){int y=1;y++;}return y;}')
        b=self.p('int f(int x){int y=0;if(x){}int y2=1;y++;return y;}')
        self.assertIsNotNone(a)
        result=compare(a,b)
        for key in ('statement_ownership','variable_scope','variable_binding','control_flow','block_boundaries'):
            self.assertEqual(result[key]['status'],'CHANGED',key)
        self.assertEqual(compare(a,a)['variable_binding']['status'],'PRESERVED')

    def test_expression_and_unsupported(self):
        a=self.p('int f(int a,int b,int c){return (a+b)*c;}')
        b=self.p('int f(int a,int b,int c){return a+b*c;}')
        self.assertEqual(compare(a,b)['expression_grouping']['status'],'CHANGED')
        for s in ('int f(int *p){return *p;}','int f(){switch(1){case 1:return 0;}}','int f(){return 0'):
            self.assertIsNone(self.p(s))
        self.assertEqual(compare(a,None)['control_flow']['status'],'UNKNOWN')

    def test_literals_and_functions(self):
        a=self.p('int f(){return 1;}')
        b=self.p('int f(){return 2;}')
        self.assertEqual(compare(a,b)['expression_grouping']['status'],'CHANGED')
        self.assertEqual(compare(a,self.p('int g(){return 1;}'))['function_boundaries']['status'],'CHANGED')


if __name__=='__main__':unittest.main()
