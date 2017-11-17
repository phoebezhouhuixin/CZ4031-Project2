import re

from utils import is_join
from utils import is_scan_node
from utils import is_branch

from nodes.hash_node import hash_node
from nodes.nested_loop import nested_loop
from nodes.merge_join import merge_join
from nodes.values_scan import values_scan
from nodes.subquery_scan import subquery_scan
from cond_parser import cond_parser

from nodes.nodes import sort
from nodes.nodes import aggregate
from nodes.nodes import materialize

from nodes.seq_scan import seq_scan
from nodes.index_scan import index_scan
from nodes.bitmap import bitmap
from nodes.cte_scan import cte_scan
from nodes.append import append
from nodes.unique import unique

from nodes.plan_limit import limit
from nodes.plan_hash_join import hash_join
from nodes.plan_result import result
from nodes.plan_function_scan import function_scan
from nodes.plan_gather import gather, gather_merge

filters = ["Filter", "Hash Cond", "Index Cond", "Merge Cond", "Recheck Cond", "Join Filter", "Sort Key", "Group Key"]
functionList ={
    'Sort': sort,
    'Aggregate': aggregate,
    'Materialize': materialize,
    'Limit': limit,
    'Hash Join': hash_join,
    'Result' : result,
    'Function Scan': function_scan,
    'Gather': gather,
    'Gather Merge': gather_merge,
    'Seq Scan': seq_scan,
    'Index Scan': index_scan,
    'Index Only Scan': index_scan,
    'BitmapAnd': bitmap,
    'BitmapOr': bitmap,
    'Bitmap Heap Scan': bitmap,
    'Bitmap Index Scan': bitmap,
    'CTE Scan': cte_scan,
    'Append': append,
    'Unique': unique,
    'Hash' : hash_node,
    'Nested Loop' : nested_loop ,
    'Merge Join':  merge_join,
    'Values Scan' : values_scan,
    'Subquery Scan' : subquery_scan,
    }

class PlanNode(object):
    def __init__(self):
        self.parent = None
        self.children = []
        self.attributes = {}
        self.nodeNumber = 0

    def explain(self):
        return functionList[self.attributes["Node Type"]](self)

        
    def get_attr(self, attr):
        if attr not in self.attributes:
            return ""
        return self.attributes[attr]

    def get_leaf(self):
        num = 0
        if(len(self.children) == 0):
            return self.nodeNumber
        for child in self.children:
            current = child.get_leaf()
            if(current > num and current - num > 1):
                num = current
        return num
    def get_branching_point(self):
        if(is_branch(self)):
            return self
        return self.parent.get_branching_point()
    
    def replacePlaceHolders(self, mapper):
        # replace the place holders with subplan results
        for filter in filters:
            attr = self.get_attr(filter)
            if(self.get_attr(filter) == ""):
                continue
            if(type(attr) is list):
                for i in range(len(attr)):
                    temp = attr[i]
                    for key, value in mapper["Subplan Results"].items():
                        self.attributes[filter][i] = temp.replace(key, value)
                    self.attributes[filter][i] = cond_parser(temp)
            else:
                for key, value in mapper["Subplan Results"].items():
                    self.attributes[filter] = attr.replace(key, value)
                self.attributes[filter] = cond_parser(attr)
        for child in self.children:
            child.replacePlaceHolders(mapper)

    def traverse(self, number, mapper, alias):      
        if(is_scan_node(self)):  
            self.nodeNumber = number
            mapper[number] = self
            
            # handle alias if this is a subquery scan
            if(alias != ""):
                self.attributes["Alias"] = alias
            return number, self
        elif(is_join(self)):
            self.nodeNumber = number
            mapper[number] = self
            nextNumber = 2 * number + 1
            maxNum, maxNode = -1, None
            for child in self.children:
                
                num, node = child.traverse(nextNumber, mapper, alias)
                nextNumber += 1
                if(num - maxNum > 1): # we prefer left node
                    maxNum = num
                    maxNode = node
            return maxNum, maxNode
        else:
            # handling alias in subquery
            if(self.get_attr("Alias") != ""):
                alias = self.get_attr("Alias")
            if(len(self.children) == 1):
                parentRelationship = self.get_attr("Parent Relationship")
                if(parentRelationship == "InitPlan"):
                    result = re.search("\$\d+", self.get_attr("Subplan Name"))
                    if(result):
                        mapper["Subplan Results"][result.group()] = self.get_attr("Output")[0]
                    return self.children[0].traverse(len(mapper["InitPlan"]), mapper["InitPlan"], alias)
                elif(parentRelationship == "SubPlan"):
                    result = self.get_attr("Subplan Name")
                    if(result):
                        mapper["Subplan Results"][result] = result
                    return self.children[0].traverse(len(mapper["SubPlan"]), mapper["SubPlan"], alias)
                return self.children[0].traverse(number, mapper, alias)
            else:
                self.nodeNumber = number
                mapper[number] = self
                maxNum, maxNode = -1, None
                for child in self.children:
                    num, node = child.traverse(number, mapper, alias)
                    if(num - maxNum > 1): # we prefer left node
                        maxNum = num
                        maxNode = node
                return maxNum, maxNode
    