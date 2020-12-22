from main.predicter import *
import unittest
import pandas as pd

class TestPredictor(unittest.TestCase):
    
    def test_create_params_p(self):
	p = .15
	N = 30
	alpha, beta = predicter.create_params (p, N)
	self.assertEqual(p, alpha/(alpha + beta))

    def test_create_params_N(self):
        p = .15
        N = 30
        alpha, beta = predicter.create_params (p, N)
        self.assertEqual(N, alpha + beta)

    def test_updateprojectection_monotonic (self):
	my_predicter = predicter("test/test.db")
        projection = my_predicter.update_projection(.5,1,10,"GSW")
	probs = projection.prob.tolist()
        decreasing = True
        last_prob = ""
	for prob in probs:
	    if last_prob == "":
	        last_prob = prob
            else:
                if prob > last_prob:
              	    decreasing  = False
                    break
                else:
                    last_prob = prob	
        self.assertTrue(decreasing)

if __name__ == '__main__':
    unittest.main()
