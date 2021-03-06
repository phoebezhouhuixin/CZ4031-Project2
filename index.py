from json_parser import JsonParser
from utils import *
from nodes.plan_cost import get_execution_cost

def get_explanation(mapper, startIndex, rootNumber, intermediate=""):
    result = ""
    current= startIndex
    while(current != rootNumber):
        if(current % 2):
            sibling = current + 1
        else:
            sibling = current - 1
        subject = "This "
        
        if(is_join(mapper[current])):
            if(not is_join(mapper[current].parent)):
                result += "The " + mapper[current].get_attr("Node Type") + " operation results will be "
                result += mapper[current].parent.explain()
        else:
            result += mapper[current].explain()

        if(is_join(mapper[current]) and is_join(mapper[sibling])):
            result += "Let's call this intermediate result as A."
            subject = "A "
            result += get_explanation(mapper, mapper[sibling].get_leaf(), sibling, "A")
            
        else:
            string = subject + "will be the " + mapper[current].get_branching_point().get_attr("Parent Relationship") + " relation of " + mapper[(current - 1) // 2].explain() + " with table "
            if(mapper[sibling].get_attr("Alias") != ""):
                string += mapper[sibling].get_attr("Alias") + ". " + mapper[sibling].get_attr("Alias") + " is retrieved with "
            else:
                string += mapper[sibling].get_attr("Relation Name") + " table. " + mapper[sibling].get_attr("Relation Name") + " is retrieved with "
            string += mapper[sibling].explain()
            result += string
        current = (current - 1) // 2

    if(rootNumber != 0):
        result += mapper[current].explain()
        result += "Let's call this intermediate result as B."
        result += "B will be the " + mapper[current].get_branching_point().get_attr("Parent Relationship") + \
        " relation of " + mapper[(current - 1) // 2].get_attr("Node Type") + \
        " with intermediate result " + intermediate + ". "
    elif(is_join(mapper[current])):
        if(mapper[current].parent != None):
            result += "The " + mapper[current].get_attr("Node Type") + " operation results will be "
            result += mapper[current].parent.explain()
    # single node like Alias, which is not join, so still need to be explained
    else:
        result += mapper[current].explain()
    return result

def get_explain_string(root):
    mapper = {"Subplan Results": {}, "InitPlan": {}, "SubPlan": {}}
    num = root.traverse(0, mapper, "", "")
    root.replacePlaceHolders(mapper)

    result = ""
    if(len(mapper["InitPlan"]) > 0):
        result += "First, the following Initial Plans are executed. "
        for k in mapper["InitPlan"].keys():
            result += mapper["InitPlan"][k].explain()
        result += "\n\n"

    if(len(mapper["SubPlan"]) > 0):
        result += "The followings are the sub plans in this query execution plan. "
        for k in mapper["SubPlan"].keys():
            result += mapper["SubPlan"][k].explain()
        result += "\n\n"

    result += "The query execution plan is as follow. "

    result += get_explanation(mapper, num, 0)
    result += "\n\n"

    columns = root.get_attr("Output")
    if(columns != ""):
        result += "We will retrieve " 
        counter = len(columns)
        for i in range(len(columns)):
            if(i != 0):
                if(i < counter - 1):
                    result += ", "
                else:
                    result += " and "
            result += columns[i] 
        result += " for the final query results. "
    result += get_execution_cost(root)
    return result

def explain(filename=None, plan=""):
    jsonParser = JsonParser(filename)
    try:
        root = jsonParser.get_tree(plan)
    except Exception as err:
        print(err)
        return "The query plan you entered is not valid!"
    return get_explain_string(root)