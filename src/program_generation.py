import random

import networkx as nx
import numpy as np
import pandas as pd


def generate_dag(n_nodes: int, p_edge: float, seed: int = None) -> nx.DiGraph:
    """Generate a random DAG with a specified number of nodes and edges.

    1. Sample a random Erdos Renyi graph with the specified number of nodes and probability of edges. The nodes in this
       graph are labelled in ascending numerical order.
    2. Convert the Erdos Renyi graph to a directed graph and remove cycles by deleting edges that point from nodes with
       a larger numerical label to nodes with a smaller numerical label (e.g. 2 --> 1).
    3. Convert exogenous nodes to inputs, labelling them in ascending order as X1, X2, ..., Xn.
    4. Convert endogenous nodes to output, labelling them in ascending order as Y1, Y2, ..., Yn.
    5. Return a networkx directed graph representing the causal DAG.

    Example output for generate_dag(n_nodes=3, p_edge=0.8):

        strict digraph  {
        X1;
        Y1;
        X2;
        X1 -> Y1;
        X2 -> Y1;
        }


    :param n_nodes: The number of nodes the DAG should contain.
    :param p_edge: The probability of edge creation.
    :param seed: An optional random seed.
    return: A string containing a DOT causal DAG.
    """
    if seed is not None:
        random.seed(seed)

    # Create an Erdos-Renyi graph with n_nodes nodes and p_edge probability of edge creation
    erdos_renyi_graph = nx.erdos_renyi_graph(n_nodes, p_edge, directed=True)

    # Convert the Erdos-Renyi graph to a directed graph and remove cycles
    causal_dag = nx.DiGraph((cause, effect) for cause, effect in erdos_renyi_graph.edges() if cause < effect)

    # Identify any deleted nodes and add to causal DAG as an isolated node
    # We will treat such nodes as inputs with no effect
    isolated_nodes = [node for node in erdos_renyi_graph.nodes if node not in causal_dag.nodes]
    causal_dag.add_nodes_from(isolated_nodes)

    # Identify input nodes (exogenous) and output nodes (endogenous)
    input_nodes = [node for node in causal_dag.nodes if not list(causal_dag.predecessors(node))]
    output_nodes = [node for node in causal_dag.nodes if node not in input_nodes]
    output_nodes.sort()

    # Rename inputs and outputs as X and Y variables, respectively
    input_node_map = {v: f"X{i+1}" for i, v in enumerate(input_nodes)}
    output_node_map = {v: f"Y{o+1}" for o, v in enumerate(output_nodes)}
    node_map = input_node_map | output_node_map
    input_output_causal_dag = nx.relabel_nodes(causal_dag, node_map)

    return input_output_causal_dag, sorted(input_node_map.values())


def generate_program(
    causal_dag: nx.DiGraph,
    p_conditional: float = 0.0,
    program_name: str = "synthetic_program",
    seed: int = None,
):
    """Generate an arithmetic python program with the same causal structure as the provided causal DAG.

    :param causal_dag: A networkx graph representing a causal DAG. This DAG will be used to produce a python program
                       with the same causal structure.
    :param p_conditional: Probability that an arbitrary node is made conditional. This will be used to create an if
                          statement.
    :param program_name: The name the program will be saved as (excluding the .py extension).
    :param seed: The seed to fix the non-deterministic behaviour.
    """
    if seed is not None:
        random.seed(seed)

    nodes_with_types = {}
    for node in causal_dag.nodes:
        n_type = "numerical"
        coin_flip = random.random()
        # Get all nodes with at least one cause
        if (causal_dag.in_degree(node) > 0) and (coin_flip < p_conditional):
            n_type = "conditional"
        nodes_with_types[node] = {"n_type": n_type}
    nx.set_node_attributes(causal_dag, nodes_with_types)

    # Construct a series of statements (program) with the same causal structure as the DAG
    statement_stack = construct_statement_stack_from_dag(causal_dag)

    # Write the program
    return write_statement_stack_to_python_file(
        statement_stack,
        sorted([node for node in causal_dag.nodes if "X" in node]),
        sorted([node for node in causal_dag.nodes if "Y" in node]),
        program_name,
    )


def construct_statement_stack_from_dag(causal_dag: nx.DiGraph):
    """Construct a stack of statements for each output in the causal DAG, with the same causal structure.

    This function iterates over the outputs in the causal DAG and constructs linear arithmetic functions with the same
    causal structure (referred to as a statement herein). For example, for {X1, X2} --> Y ==> Y = (2*X1) + (-4*X2) + 10.

    Our algorithm starts by constructing statements for terminal outputs and then proceeds to intermediate outputs.
    This results in a stack of statements that, upon reversal, can be piped into a python file to form the body of an
    executable function with the same causal structure as the specified causal DAG.

    :param causal_dag: A networkx DiGraph representing a causal DAG from which the structure of the program will be
                       generated.
    :return: A list of strings representing statements that can be executed in python.
    """
    nodes_ordered_for_traversal = reversed([node for node in nx.topological_sort(causal_dag) if "Y" in node])
    statement_stack = []

    for output_node in nodes_ordered_for_traversal:

        # Construct a linear equation for each node based on its causes
        causes = [cause for (cause, effect) in causal_dag.in_edges(output_node)]

        # Add if not none before each output statement for controllability
        # statement = f"\tif {output_node} is None:\n"
        statement = ""

        # Add conditional behaviour for conditional nodes
        if causal_dag.nodes[output_node]["n_type"] == "conditional":

            # Take a random subset (comprising at least one node) of the conditional node's parents
            n_causes_to_sample = random.randint(1, len(causes))
            causes_to_include_in_predicate = random.sample(causes, n_causes_to_sample)

            # Place the linear equation within an if statement whose predicate is a function of all conditional causes
            inequality = generate_predicate(causes_to_include_in_predicate)
            if_body_statement, else_body_statement = generate_if_else_body(causes, causes_to_include_in_predicate)
            statement += f"\t{output_node} = np.where({inequality}, {if_body_statement}, {else_body_statement})\n"

        else:
            # No conditional parents so no if-then-else
            statement += f"\t{output_node} = {generate_linear_statement(causes)}\n"
        statement_stack.append(statement)

    return statement_stack


def generate_linear_statement(causes: list[str]):
    """Generate a random linear statement of the effect node that includes all of the causes.

    Example: Y = (2 * X1) + (3 * X2) + (-4 * X3) + 4 for effect=Y and causes=[X1, X2, X3].

    :param causes: Nodes to appear on RHS of statement.
    :return statement: A string representing a linear statement in Python.
    """
    coefficients = [random.choice([random.randint(1, 10), random.randint(-10, -1)]) for _ in causes]
    expr = " + ".join([f"({c} * {x})" for c, x in zip(coefficients, causes)])
    expr += f" + {random.choice([random.randint(0, 10), random.randint(-10, 0)])}"
    return f"({expr}) * np.random.normal(loc=1, scale=0.10)"


def generate_predicate(conditional_causes: list[str]):
    """Generate a predicate from a list of conditional causes.

    The predicate is an inequality that checks whether the sum of conditional causes is either greater than or equal to
    or less than or equal to some value in the range [-10, 10].

    Example: if (X1 + X2 + X3 >= 4): for conditional_causes = [X1, X2, X3].

    :param conditional_causes: A list of variables that are to be used in the predicate.
    :return predicate: A predicate that is a function of all given conditional causes.
    """
    inequality_symbol = random.choice([" <= ", " >= "])
    inequality_value = random.randint(-10, 10)
    inequality = " + ".join([f"{x}" for x in conditional_causes]) + inequality_symbol + str(inequality_value)
    return inequality


def generate_if_else_body(causes: list[str], conditional_causes: list[str]):
    """Generate a pair of statements for the if and else body corresponding to a particular cause-effect relationship.

    This method generates a statement for the true branch of the if statement that includes a random (potentially empty)
    subset of the effect node's causes.

    To guarantee the causal structure of the program contains all causes of the effect, this method then generates an
    else statement that includes all causes of the effect node that did not appear in the true branch of the i
    statement. In addition to these necessary nodes, the statement in the else body also includes a random (potentially
    empty) subset of the effect node's causes.

    :param causes: The variables that appear on the RHS of the statement.
    :param conditional_causes: The parents of the effect variable that are conditional (i.e. appear in the predicate of
                               the if statement).
    :return if_body_statement, else_body_statement: The statement for the true and false branches of the if statement,
                                                    respectively.
    """
    # Sample a potentially empty set of causes to include in the if body's statement
    if_body_nodes = random.sample(causes, random.randint(0, len(causes)))
    if_body_statement = generate_linear_statement(if_body_nodes)

    # The else body statement must include at least all causes that do not appear in the if statement
    necessary_else_body_nodes = set(causes) - set(if_body_nodes) - set(conditional_causes)

    # The else body statement's nodes can also overlap with the if body statement's nodes
    nodes_not_in_else_body = set(causes) - necessary_else_body_nodes
    additional_else_body_nodes = random.sample(
        sorted(nodes_not_in_else_body), random.randint(0, len(nodes_not_in_else_body))
    )
    else_body_nodes = list(necessary_else_body_nodes) + additional_else_body_nodes

    # Confirm that all causes are used in either the if statement, else statement, or predicate
    assert set(else_body_nodes + if_body_nodes + conditional_causes) == set(causes), (
        f"Error, the following causes are missing: "
        f"{set(causes) - set(else_body_nodes + if_body_nodes + conditional_causes)}"
    )

    else_body_statement = generate_linear_statement(else_body_nodes)

    return if_body_statement, else_body_statement


def write_statement_stack_to_python_file(
    statement_stack: list[str],
    sorted_input_nodes: list[str],
    sorted_output_nodes: list[str],
    program_name: str,
):
    """Convert a statement stack to a python program.

    :param statement_stack: A list of syntax trees that can be executed in python.
    :param sorted_input_nodes: A list of inputs sorted in ascending numerical order (i.e. X1, X2, X3 ...)
    :param sorted_output_nodes: A list of outputs sorted in ascending numerical order (i.e. Y1, Y2, Y3 ...)
    :param program_name: A name for the generated python file (excluding the .py extension).
    """
    input_args_str = "".join([f"\t{x}: int,\n" for x in sorted_input_nodes])
    method_definition_str = f"def {program_name}(\n{input_args_str}):\n"
    return_str = (
        "\treturn {" + "".join([f"'{y}': {y}, " for y in sorted_input_nodes + sorted_output_nodes])[:-2] + "}\n"
    )
    statement_stack.reverse()  # Reverse the statement stack to be in order of execution (later outputs last)

    method = method_definition_str + "\n".join(statement_stack) + return_str

    namespace = {"np": np}

    with open("/tmp/program.py", "w") as f:
        f.write(method)
    exec(method, namespace)
    return namespace[program_name]


def dag_and_data(n_nodes: int, p_edge: float, p_conditional: float, num_points: int, seed: int):
    """
    Generate a causal DAG and associated dataset.
    """

    np.random.seed(seed)

    dag, inputs = generate_dag(n_nodes=n_nodes, p_edge=p_edge, seed=seed)
    function = generate_program(dag, p_conditional=p_conditional, program_name="program")
    data = pd.DataFrame(function(**{x: np.random.rand(num_points) * 100 for x in inputs}))

    # output_columns = [column for column in data if column.startswith("Y")]
    # data[output_columns] += np.random.normal(
    #     loc=0,
    #     scale=0.10 * (data[output_columns].max() - data[output_columns].min()),
    #     size=(len(data), len(output_columns)),
    # )
    # data[output_columns] += np.random.normal(loc=0, scale=0.10 * data[output_columns].abs())

    return dag, data
