Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).
Do NOT use graphlib or any external library. Implement the algorithm yourself.

Implement exactly one public function:

    def toposort(graph: dict) -> list | None

`graph` maps a node (str) to a list of nodes (str) it DEPENDS ON (its prerequisites): an edge
u -> v in the returned order means every dependency of a node appears BEFORE that node.

Return a list of all nodes in a valid dependency order, or None if the graph has a cycle.

Rules (follow exactly):
- Every node that appears anywhere — as a key OR inside any dependency list — must appear exactly
  once in the output. A dependency named but absent as a key is a valid node with no dependencies.
- Ordering: a node may be emitted only after ALL of its dependencies have been emitted.
- DETERMINISTIC TIE-BREAK: whenever more than one node is eligible to be emitted next (all its
  dependencies already emitted), choose the one that is smallest in ascending string (Unicode
  code point) order. This makes the output unique for a given graph.
- Duplicate dependencies in a list (e.g. {"a": ["b","b"]}) are treated as one edge.
- A self-loop ({"a": ["a"]}) is a cycle -> return None.
- The empty graph {} returns [].
- Any cycle anywhere -> return None (even if part of the graph is acyclic).

Correctness note: the classic bug is using only the keys as the node set, or a non-deterministic
tie-break. Both are wrong here. Also: emitting a node before a dependency that itself has no key
entry is wrong — absent-as-key still means it must precede its dependents.

The function must never raise for a well-typed `graph` (dict of str -> list of str).
Pure computation, no I/O.
