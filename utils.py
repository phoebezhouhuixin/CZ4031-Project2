import random
def is_scan_node(planTree):
    node = planTree.get_attr("Node Type")
    #TODO: do we need to include Subquery Scan?
    #TODO: Is bitmap heap scan a scan node? or always after bitmap index scan?
    if(node in ["Seq Scan", "Index Scan", "Values Scan", "Bitmap Index Scan", "Index Only Scan"]):
        return True
    return False

def get_conjuction():
    return random.choice(["and in the end ", "and ultimately ", "and subsequently ", "and finally ", "and eventually "])

def is_join(planTree):
    if(planTree == None):
        return True
    if(planTree.get_attr("Node Type") in ["Hash Join", "Merge Join", "Nested Loop", "Append"]):
        return True
    return False

def is_branch(planTree):
    if(planTree.parent == None):
        return True
    #return len(planTree.children) > 1
    return is_join(planTree.parent) or planTree.get_attr("Parent Relationship") == "InitPlan" or planTree.get_attr("Parent Relationship") == "SubPlan"
