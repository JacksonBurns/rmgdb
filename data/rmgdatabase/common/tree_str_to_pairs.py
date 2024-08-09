# turn the tree strings into pairs of nodes


# went to all the trouble of massaging the string into a nested dict since
# the nested dict representation of a tree can easily be parsed for all the node pairs
# i.e. even ChatGPT can do it
def get_node_pairs(tree_dict, parent=None):
    node_pairs = []

    for node, children in tree_dict.items():
        node_pairs.append((parent, node))

        if children:
            child_pairs = get_node_pairs(children, parent=node)
            node_pairs.extend(child_pairs)
        else:
            node_pairs.append((node, None))

    return node_pairs


def sketchy_conversion(instr):
    # first parse the tree into dict
    overall_dict = {}
    added_stack = []
    last_level = 0
    for line in instr.split("\n"):
        if "L" not in line:
            continue
        level = (len(line) - len(line.lstrip(" "))) // 4
        group = line.split(": ")[1]

        if level == 0:
            overall_dict[group] = {}
            added_stack = [group]
        elif level > last_level:  # move right
            temp = overall_dict
            for nav_group in added_stack:
                temp = temp[nav_group]
            temp[group] = {}
            added_stack.append(group)
            last_level = level
        elif level == last_level:  # move down
            temp = overall_dict
            added_stack.pop()
            for nav_group in added_stack:
                temp = temp[nav_group]
            temp[group] = {}
            added_stack.append(group)
        else:  # move left
            added_stack.pop()
            for _ in range(last_level - level):
                added_stack.pop()
            temp = overall_dict
            for nav_group in added_stack:
                temp = temp[nav_group]
            temp[group] = {}
            added_stack.append(group)
            last_level = level

    # print("\n\nresult")
    # import json

    # print(json.dumps(overall_dict, indent=2))
    return get_node_pairs(overall_dict)


if __name__ == "__main__":
    test_str = """
L1: carbene
L1: RR'
    L2: R_H
        L3: H2
        L3: Ct_H
            L4: acetylene
        L3: RO_H
            L4: CsO_H
        L3: RS_H
            L4: CsS_H
        L3: Cd_H
            L4: Cd_pri
                L5: ethene
            L4: Cd_sec
                L5: Cd/H/NonDeC
                L5: Cd/H/NonDeO
                L5: Cd/H/NonDeS
                L5: Cd/H/OneDe
        L3: Cb_H
        L3: Cs_H
            L4: C_methane
            L4: C_pri
                L5: C_pri/NonDeC
                L5: C_pri/NonDeO
                L5: C_pri/NonDeS
                L5: C_pri/De
                    L6: C_pri/Cd
                    L6: C_pri/Ct
            L4: C_sec
                L5: C/H2/NonDeC
                L5: C/H2/NonDeO
                    L6: C/H2/CsO
                    L6: C/H2/O2
                L5: C/H2/NonDeS
                    L6: C/H2/CsS
                    L6: C/H2/S2
                L5: C/H2/OneDe
                    L6: C/H2/OneDeC
                    L6: C/H2/OneDeO
                    L6: C/H2/OneDeS
                L5: C/H2/TwoDe
            L4: C_ter
                L5: C/H/NonDeC
                    L6: C/H/Cs3
                    L6: C/H/NDMustO
                    L6: C/H/NDMustS
                L5: C/H/OneDe
                    L6: C/H/Cs2
                    L6: C/H/ODMustO
                    L6: C/H/ODMustS
                L5: C/H/TwoDe
                    L6: C/H/Cs
                    L6: C/H/TDMustO
                    L6: C/H/TDMustS
                L5: C/H/ThreeDe
    L2: R_R'
        L3: Cs_Cs
            L4: C_methyl_C_methyl
            L4: C_methyl_C_pri
            L4: C_methyl_C_sec
            L4: C_methyl_C_ter
        L3: Cs_Cd
            L4: C_methyl_Cd_pri
            L4: C_methyl_Cd_sec
        L3: Cs_Cb
"""
    print(sketchy_conversion(test_str))
