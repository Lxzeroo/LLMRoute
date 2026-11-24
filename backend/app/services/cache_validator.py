import re
from collections import Counter
class CacheValidator:
    volatile={'today','tomorrow','yesterday','latest','current','currently','now','live','recent','tonight'}
    negations={'not','never','no','without','cannot',"isn't","aren't","don't","doesn't","won't","can't"}
    groups=[{'what','explain','define','describe'},{'compare','difference','versus','vs'},{'calculate','compute','solve'},{'implement','build','create','write','generate'},{'debug','fix','error','troubleshoot'}]
    def words(self,text):
        return {t[:-2] if t.endswith("'s") else t for t in re.findall(r"\b[\w']+\b",text.lower().replace('\u2019',"'"))}
    def cacheable(self,query): return not bool(self.words(query)&self.volatile)
    def validate(self,query,cached):
        a,b=self.words(query),self.words(cached)
        if not self.cacheable(query) or not self.cacheable(cached): return False,'Volatile query'
        if Counter(re.findall(r'[+-]?\d+(?:\.\d+)*%?',query))!=Counter(re.findall(r'[+-]?\d+(?:\.\d+)*%?',cached)): return False,'Numerical mismatch'
        if a&self.negations != b&self.negations: return False,'Negation mismatch'
        x={i for i,g in enumerate(self.groups) if a&g}; y={i for i,g in enumerate(self.groups) if b&g}
        if x and y and x.isdisjoint(y): return False,'Intent mismatch'
        return True,'Validation passed'
cache_validator=CacheValidator()
