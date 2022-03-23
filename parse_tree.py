from __future__ import annotations

import NLI_hyponomy_analysis.data_pipeline.matrix_operations.hyponymy_library as hl

from nltk import Tree
from functools import reduce
from typing import Callable, List
import numpy as np


class ChildAlreadyExistsError(Exception):
    def __init__(self, child, new_child):
        self.message = f"The node already has child {child}. Cannot insert {new_child}"
        super(ChildAlreadyExistsError, self).__init__(self.message)


class ParseTree:
    ignore_labels = ['ls', 'pos', '.', 'dt', ',']
    hadamard_labels = ['ex', 'cd', 'md', 'pdt', 'prp', 'prp$', 'rp', 'uh', 'to']
    adjective_labels = ['in', 'jj']

    def __init__(self, binary_parse_string, word_vectors, default_op=hl.mult):
        self.data = self.pos_string_to_binary_tree(binary_parse_string)
        self.default_op = default_op
        self.word_vectors = word_vectors

    def __repr__(self):
        return self.data.__repr__()

    def evaluate(self) -> None:
        self.data = self.__evaluate(self.data)
        return None

    def tree_to_binary(self, tree):
        """
        Recursively turn a tree into a binary tree.
        """
        if isinstance(tree, str):
            return tree
        elif len(tree) == 1:
            return self.tree_to_binary(tree[0])
        else:
            label = tree.label()
            return reduce(lambda x, y: Tree(label, (self.tree_to_binary(x), self.tree_to_binary(y))), tree)

    @classmethod
    def from_sentence(cls, sentence: str, word_vectors, delimiter=' ', tags=None):
        if '(' not in sentence:
            output = ParseTree('()', word_vectors)
            leaves = sentence.split(delimiter)
            if tags is None:
                leaves = [Tree('', [leaf]) for leaf in leaves]
            else:
                assert len(tags) == len(leaves), TypeError
                leaves = [Tree(tag, [leaf]) for tag, leaf in zip(tags, leaves)]
            output.data = Tree("Root", leaves)
            return output
        return ParseTree(sentence, word_vectors)

    def __binary_operation(self, label1: str, label2: str) -> Callable[[np.array, np.array], np.array]:
        if label1 in self.ignore_labels:
            if label2 in self.ignore_labels:
                return lambda x, y: None
            return lambda x, y: y
        if label2 in self.ignore_labels:
            return lambda x, y: x

        return self.default_op

    def __evaluate(self, tree: Tree):
        """
        We maintain a stack of parents.
        If all the children in the current node are leaves, we operate on tree1, tree2, tree3, ...
        """

        tree_list = []
        for child in tree:
            if self.__tree_is_leaf(child):
                tree_list.append(child)
            else:
                tree_list.append(self.__evaluate(child))

        if len(tree_list) == 1:
            vector1 = tree_list[0][0]
            if isinstance(vector1, str):
                vector1 = self.word_vectors.safe_lookup(vector1)
            return Tree(tree.label(), [vector1])

        if len(tree_list) == 2:
            return self.__evaluate_2(tree_list[0], tree_list[1], tree.label())

        return self.__evaluate_greater_than_2(tree_list, tree.label())

    def __evaluate_2(self, tree1: Tree, tree2: Tree, parent_label: str) -> Tree:
        label1 = tree1.label()
        label2 = tree2.label()

        vector1 = tree1[0]
        if isinstance(vector1, str):
            vector1 = self.word_vectors.safe_lookup(tree1[0])

        vector2 = tree2[0]
        if isinstance(vector2, str):
            vector2 = self.word_vectors.safe_lookup(tree2[0])

        operation = self.__binary_operation(label1, label2)

        if vector1 is None:
            if vector2 is None:
                return Tree(parent_label, [None])
            return Tree(parent_label, [vector2])
        if vector2 is None:
            return Tree(parent_label, [vector1])

        return Tree(parent_label, [operation(vector1, vector2)])

    def __evaluate_greater_than_2(self, tree_list: List[Tree], parent_label: str) -> Tree:
        assert len(tree_list) > 2, ValueError

        if self.__contains_adjective(tree_list):
            # Go right to left evaluation using projection
            previous_default_op = self.default_op
            self.default_op = hl.mmult1
            evaluated_tree = self.__evaluate_right2left(tree_list)
            self.default_op = previous_default_op
            return Tree(parent_label, [evaluated_tree[0]])

        evaluated_tree = self.__evaluate_left2right(tree_list)
        return Tree(parent_label, [evaluated_tree[0]])

    def __evaluate_left2right(self, tree_list: List[Tree]) -> Tree:
        current_tree = tree_list[0]
        for tree in tree_list[1:]:
            current_tree = self.__evaluate_2(current_tree, tree, current_tree.label())
        return current_tree

    def __evaluate_right2left(self, tree_list: List[Tree]) -> Tree:
        current_tree = tree_list[-1]
        for tree in reversed(tree_list[:-1]):
            current_tree = self.__evaluate_2(tree, current_tree, current_tree.label())
        return current_tree

    def __contains_adjective(self, tree_list: List[Tree]) -> bool:
        has_adjective = False
        for tree in tree_list:
            if self.__is_adjective(tree.label()):
                has_adjective = True
                break
        return has_adjective

    @staticmethod
    def __is_verb(label: str) -> bool:
        if label == '':
            return False
        if label[0].lower() == 'v':
            return True
        return False

    @staticmethod
    def __is_noun(label: str) -> bool:
        if label == '':
            return False
        test_label = label.lower()
        if test_label[0] == 'n':
            return True
        if test_label == 'wp':
            return True
        return False

    def __is_adjective(self, label: str) -> bool:
        if label == '':
            return False
        if label.lower() in self.adjective_labels:
            return True
        return False

    @staticmethod
    def __tree_is_leaf(tree: Tree):
        if len(tree) == 1:
            if not isinstance(tree[0], Tree):
                return True
        return False

    @staticmethod
    def pos_string_to_binary_tree(pos_string: str):
        parsed_tree = Tree.fromstring(pos_string, remove_empty_top_bracketing=False)
        return parsed_tree


def main():
    pass


if __name__ == "__main__":
    pass