def bitmap(tree):
    operation_name = tree.get_attr("Node Type")

    msg = "The DBMS performs {} {}\n".format(operation_name, get_message(tree))

    for child in tree.children:
        msg += child.explain()

    return msg

def get_message(tree):
    msg = ""
    node = tree.get_attr("Node Type")

    if "Heap" in node:
        msg += "on table {} with recheck condition {}".format(tree.get_attr("Relation Name"), tree.get_attr("Recheck Cond"))
    elif "Index" in node:
        msg += "on index {} with index condition {}".format(tree.get_attr("Index Name"), tree.get_attr("Index Cond"))

    return msg