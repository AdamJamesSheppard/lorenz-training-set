"""Build/check/search the Git-backed research graph using only Python stdlib."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.research_graph import (  # noqa: E402
    GRAPH_PATH, build_graph, check_graph, search, walk,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true', help='Regenerate derived graph, never evidence')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--search', default='')
    parser.add_argument('--kind')
    parser.add_argument('--status', help='Exact status, e.g. PASSED, FAILED, OPEN, NUMERICAL')
    parser.add_argument('--show', help='Exact stable node ID')
    parser.add_argument('--neighbors', help='Exact stable node ID')
    parser.add_argument('--path', nargs=2, metavar=('FROM_ID', 'TO_ID'))
    parser.add_argument('--depth', type=int, default=2)
    parser.add_argument('--direction', choices=['both', 'out', 'in'], default='both')
    parser.add_argument('--relation', action='append', help='Restrict traversal; repeat for multiple types')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    if args.build:
        graph = build_graph(ROOT)
        (ROOT / GRAPH_PATH).write_text(json.dumps(graph, indent=2, ensure_ascii=False)+'\n')
        print(f"Graph generated: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    if args.check:
        errors = check_graph(ROOT)
        print('\n'.join(errors) if errors else 'RESEARCH GRAPH: PASS (documentary provenance only)')
        return int(bool(errors))
    graph = json.loads((ROOT / GRAPH_PATH).read_text())
    by_id = {n['id']: n for n in graph['nodes']}
    try:
        if args.show:
            if args.show not in by_id:
                raise ValueError('Unknown exact node ID')
            print(json.dumps(by_id[args.show], indent=2, ensure_ascii=False))
        elif args.path:
            result = walk(graph, args.path[0], args.depth, args.direction,
                          args.path[1], args.relation)
            if result is None:
                print('No path within requested depth/direction/relation scope')
                return 1
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.neighbors:
            result = walk(graph, args.neighbors, args.depth, args.direction, relations=args.relation)
            items = [dict(node=by_id[key], path=path) for key, path in result.items()]
            shown = items[:args.limit]
            if args.json:
                print(json.dumps(dict(total=len(items), shown=shown), indent=2, ensure_ascii=False))
            else:
                for item in shown:
                    node = item['node']
                    route = ' / '.join(p['relation'] for p in item['path']) or 'START'
                    print(f"{node['id']} [{node.get('status', node['kind'])}] via {route}")
                print(f'Shown {len(shown)} of {len(items)} reachable nodes; use --limit to expand')
        else:
            result = search(graph, args.search, args.kind, args.status)
            shown = result[:args.limit]
            if args.json:
                print(json.dumps(dict(total=len(result), shown=shown), indent=2, ensure_ascii=False))
            else:
                for item in shown:
                    print(f"{item['id']} [{item.get('status', item['kind'])}] {item['label']}")
                print(f'Shown {len(shown)} of {len(result)} matches; use --limit to expand')
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
