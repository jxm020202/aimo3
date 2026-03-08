# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from transformers import AutoModelForCausalLM, AutoTokenizer
import random
import re
import torch


PROMPT = """You will be given a challenging math problem followed by {num_solutions} solutions. Your task is to systematically analyze these solutions to identify the most mathematically sound approach.

Input Format:
Problem: A complex mathematical word problem at advanced high school or college level
Solutions: Detailed solutions indexed 0-{max_idx}, each concluding with an answer in \\boxed{{}} notation

YOUR TASK

Problem: {problem}

Solutions:
{solutions}

Evaluation Process:

1. Initial Screening
- Group solutions by their final answers
- Identify and explain mathematical contradictions between different answers
- Eliminate solutions with clear mathematical errors

2. Detailed Analysis
For remaining solutions, evaluate:
- Mathematical precision and accuracy
- Logical progression of steps
- Completeness of mathematical reasoning
- Proper use of mathematical notation, including \\boxed{{}}
- Handling of edge cases or special conditions
- For solutions containing and addressing errors, evaluate the error identification and correction methodology.

3. Solution Comparison
Compare viable solutions based on:
- Efficiency of approach
- Clarity of mathematical reasoning
- Sophistication of method
- Robustness of solution (works for all cases)

Your response should include:
1. Brief analysis of conflicting answers
2. Detailed evaluation of mathematically sound solutions
3. Justification for eliminating incorrect solutions
4. Clear explanation for selecting the best approach

End your evaluation with exactly:
Judgment: [IDX]
where IDX is the index 0-{max_idx} of the best solution.
"""


PROBLEM = """In an $11 \\times 11$ grid of cells, each pair of edge-adjacent cells is connected by a door. Karthik wants to walk a path in this grid. He can start in any cell, but he must end in the same cell he 
started in, and he cannot go through any door more than once (not even in opposite directions). Compute the maximum number of doors he can go through in such a path."""


SOLUTION_LIST = [
    """The grid is \\(11 \\times 11\\), so there are \\(11 \\times 11 = 121\\) cells. The total number of doors (edges) is calculated as follows:  \n- Horizontal doors: 11 rows with 10 doors each, so \\(1
1 \\times 10 = 110\\).  \n- Vertical doors: 11 columns with 10 doors each, so \\(11 \\times 10 = 110\\).  \nTotal doors: \\(110 + 110 = 220\\).  \n\nKarthik must walk a closed path (cycle) starting and ending at th
e same cell, without reusing any door. The goal is to maximize the number of doors used, which corresponds to finding a subgraph that is connected, has all even degrees (to admit an Eulerian circuit), and maximizes
 the number of edges.  \n\nThe grid has 36 vertices of odd degree:  \n- Each side has \\(11 - 2 = 9\\) edge cells (not corners) with degree 3.  \n- With 4 sides, total odd-degree vertices: \\(4 \\times 9 = 36\\).  
\n\nTo make all degrees even, edges must be removed. The minimum number of edges to remove to achieve an Eulerian circuit in a connected graph is given by a minimum T-join, where T is the set of odd-degree vertices
. For an \\(n \\times n\\) grid with \\(n\\) odd, the minimum number of edges to remove is \\(4n - 8\\). For \\(n = 11\\):  \n\\[4 \\times 11 - 8 = 44 - 8 = 36.\\]  \n\nThus, 36 edges must be removed. The remaining
 number of edges is:  \n\\[220 - 36 = 184.\\]  \n\nThis is achievable with the following construction:  \n1. On each boundary (top, bottom, left, right), remove 4 horizontal or vertical edges to pair adjacent odd-d
egree cells, covering 8 cells per boundary and leaving one unpaired per boundary. This removes \\(4 \\times 4 = 16\\) edges.  \n   - The unpaired cells are \\((1,10)\\), \\((11,10)\\), \\((10,1)\\), and \\((10,11)\
\).  \n2. Pair \\((11,10)\\) and \\((10,11)\\) by removing a path of length 2 (e.g., edges \\((11,10)-(10,10)\\) and \\((10,10)-(10,11)\\)).  \n3. Pair \\((1,10)\\) and \\((10,1)\\) by removing a path of length 18 
(e.g., vertically down column 10 from \\((1,10)\\) to \\((10,10)\\), then horizontally left in row 10 from \\((10,10)\\) to \\((10,1)\\)).  \n   - This removes \\(2 + 18 = 20\\) edges.  \nTotal edges removed: \\(16
 + 20 = 36\\).  \n\nThe remaining graph has 184 edges, is connected, and has all even degrees, so an Eulerian circuit exists with 184 edges. This is the maximum possible, as fewer removals would leave odd-degree ve
rtices or disconnect the graph.  \n\n\\boxed{184}""",
    """The problem involves finding the maximum number of doors Karthik can traverse in an \\(11 \\times 11\\) grid, starting and ending at the same cell, without repeating any door (edge adjacency).\n\nT
he grid has \\(11 \\times 11 = 121\\) cells. The total number of doors (edges) is calculated as follows:\n- Horizontal doors: \\(11\\) rows, each with \\(10\\) doors, so \\(11 \\times 10 = 110\\).\n- Vertical doors
: \\(11\\) columns, each with \\(10\\) doors, so \\(11 \\times 10 = 110\\).\n- Total doors: \\(110 + 110 = 220\\).\n\nThe grid graph is connected and bipartite, with a chessboard coloring. The number of black cells
 is \\(61\\) and white cells is \\(60\\), since both dimensions are odd. The degrees of the vertices vary:\n- Corner cells have degree \\(2\\) (even).\n- Edge cells (not corners) have degree \\(3\\) (odd).\n- Inter
nal cells have degree \\(4\\) (even).\n\nThe number of odd-degree vertices (denoted \\(S\\)) is:\n- Top row: \\(11 - 2 = 9\\) (excluding corners).\n- Bottom row: \\(9\\).\n- Left column: \\(9\\) (excluding corners)
.\n- Right column: \\(9\\).\n- Total: \\(9 + 9 + 9 + 9 = 36\\).\n\nKarthik's path is a closed trail (start and end at the same vertex, no repeated edges, but vertices may be revisited). The maximum number of edges 
in such a trail corresponds to the size of the largest connected Eulerian subgraph (all degrees even and connected).\n\nFor an \\(m \\times n\\) grid with both dimensions odd, the minimum number of edges to remove 
to make the graph Eulerian (all degrees even) is \\(m + n - 2\\). Here, \\(m = n = 11\\), so:\n\\[\nm + n - 2 = 11 + 11 - 2 = 20.\n\\]\nAfter removing these 20 edges, the remaining graph has:\n\\[\n220 - 20 = 200\n
\\]\nedges. This subgraph is connected and Eulerian, so it admits an Eulerian circuit (a closed trail) using all 200 edges.\n\nIt is not possible to have a closed trail with more than 200 edges, as removing fewer t
han 20 edges cannot make all degrees even (since at least 20 edges must be removed to address the 36 odd-degree vertices, and the minimum is 20 for this grid).\n\nThus, the maximum number of doors Karthik can trave
rse is 200.\n\n\\boxed{200}""",
    """The grid is an $11 \\times 11$ graph with cells as vertices and doors between edge-adjacent cells as edges. The graph is bipartite, with partitions of sizes 61 and 60 due to the odd grid size. A cy
cle must alternate between the two partitions, so the maximum number of vertices in any cycle is $2 \\times \\min(61, 60) = 120$.\n\nThis maximum is achievable by removing one vertex from the partition of size 61, resulting in a graph with 60 vertices in each partition. The remaining graph is Hamiltonian, meaning it contains a cycle that visits each vertex exactly once. For an $11 \\times 11$ grid with one vertex removed, su
ch a cycle exists, as the grid remains connected and satisfies the conditions for Hamiltonicity when a single cell is removed (given the grid dimensions are at least $2 \\times 2$).\n\nA cycle with 120 vertices has
 120 edges, as the number of edges equals the number of vertices in a cycle. Since each edge corresponds to a door, the maximum number of doors Karthik can traverse in a closed path without reusing any door is 120.
\n\n\\boxed{120}""",
    """The grid is an $11 \\times 11$ graph, which is bipartite due to its chessboard coloring. The total number of cells is $11 \\times 11 = 121$. In this coloring, one color class has 61 cells and the o
ther has 60 cells, as determined by the grid's odd size.\n\nA cycle in a bipartite graph must have an equal number of vertices from each color class. Therefore, the maximum number of vertices in any cycle is $2 \\t
imes \\min(61, 60) = 2 \\times 60 = 120$. This implies that the maximum cycle length in terms of vertices is 120.\n\nSince the number of edges in a cycle equals the number of vertices, the maximum number of edges (
doors) in a cycle is also 120. This maximum is achievable by removing one black vertex (from the color class with 61 vertices), specifically the center cell at $(6,6)$, and finding a Hamiltonian cycle on the remaining 120-vertex graph. The grid remains connected after removing the center, and such a cycle exists for an $n \\times n$ grid with $n$ odd by removing the center cell.\n\nThus, the maximum number of doors Karthik can traverse in a closed path without repeating any door is 120.\n\n\\boxed{120}""",
]


MODEL_NAME = "nvidia/OpenReasoning-Nemotron-7B"
MAX_NEW_TOKENS = 32000


def load_model(model_name):
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer


def format_prompt(problem, solutions, num_solutions):
    prompt = PROMPT.format(problem=problem, solutions=solutions, num_solutions=num_solutions, max_idx=num_solutions - 1)
    return prompt


def format_solutions(solution_list):
    solutions = "\n".join([f"Solution {i}: {solution}" for i, solution in enumerate(solution_list)])
    return solutions


def get_prompt():
    problem = PROBLEM
    solutions = format_solutions(SOLUTION_LIST)
    num_solutions = len(SOLUTION_LIST)
    prompt = format_prompt(problem, solutions, num_solutions)
    return prompt, num_solutions


def generate_response(model, tokenizer, prompt):
    chat = [{"role": "user", "content": prompt}]
    input_ids = tokenizer.apply_chat_template(
        chat,
        return_tensors="pt"
    )
    outputs = model.generate(
        input_ids.to(model.device), 
        max_new_tokens=MAX_NEW_TOKENS, 
        temperature=0.6, 
        top_p=0.95, 
        do_sample=True,
        use_cache=True,
        eos_token_id=tokenizer.eos_token_id, 
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def extract_judgment(generation, max_idx=None):
    """Extract the judgment from the generation."""
    judgment = None

    try:
        matches = re.findall(r"Judg[e]?ment: (\d+)", generation)

        if matches:
            number = matches[-1]
            judgment = int(number)
            if max_idx is not None and judgment > max_idx:
                judgment = None
        else:
            judgment = None

    except:
        judgment = None

    if judgment is not None and max_idx is not None:
        if judgment > max_idx:
            judgment = None

    return judgment


def main():
    # Load model
    model, tokenizer = load_model(MODEL_NAME)
    # Construct prompt
    prompt, num_solutions = get_prompt()
    # Get response
    response = generate_response(model, tokenizer, prompt)
    # Extract judgment
    judgment = extract_judgment(response, max_idx=num_solutions - 1)
    # Print judgment
    print("Selected solution index:", judgment)
    if judgment is not None:
        print("Chosen solution:", SOLUTION_LIST[judgment])
    else:
        print("No solution selected")


if __name__ == "__main__":
    main()