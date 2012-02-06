#!/usr/bin/env python

import re, math

def get_words(doc):
    splitter = re.compile('\\W*')
    words = [s.lower() for s in splitter.split(doc) \
            if len(s) > 2 and len(s) < 20]
    return dict([(w,1) for w in words])

def sampletrain(cl):
    cl.train('Nobody owns the water.','good')
    cl.train('the quick rabbit jumps fences','good')
    cl.train('buy pharmaceuticals now','bad')
    cl.train('make quick money at the online casino','bad')
    cl.train('the quick brown fox jumps','good')

class Classifier:
    def __init__(self, get_features, file_name=None):
        # Feature <-> category count
        self.fc = {}
        # Categories count
        self.cc = {}
        # Extract features from document
        self.get_features = get_features
        
    # Increase feature-category count    
    def inc_f(self, f, cat):
        # If f and cat are absent from our maps put them in
        self.fc.setdefault(f, {})
        self.fc[f].setdefault(cat, 0)
        self.fc[f][cat]  += 1
    
    def inc_c(self, cat):
        self.cc.setdefault(cat, 0)
        self.cc[cat] += 1
    
    def f_count(self, f, cat):
        if f in self.fc and cat in self.fc[f]:
            return float(self.fc[f][cat])
        else:
            return 0.0
    
    def c_count(self, cat):
        if cat in self.cc:
            return float(self.cc[cat])
        else:
            return 0.0
    
    def total_count(self):
        return sum(self.cc.values())

    def categories(self):
        return self.cc.keys()

    def train(self, item, cat):
        features = self.get_features(item)
        for f in features:
            self.inc_f(f, cat)
        self.inc_c(cat)    
        return

    def f_prob(self, f, cat):
        if self.c_count(cat) == 0:
            return 0
        else:
            # Pr(f|c) = Pr(f and c)/Pr(c)
            return self.f_count(f, cat)/self.c_count(cat)
    
    def get_weighted_prob(self, f, cat, prf, weight=1.0, ap=0.5):
        basic_prob = prf(f, cat)
        totals = sum([self.f_count(f,c) for c in self.categories()])
        bp = ((weight*ap) + (totals*basic_prob))/(weight*totals)
        return bp


