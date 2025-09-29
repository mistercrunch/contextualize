#!/usr/bin/env python3
"""
Web-based DAG visualizer for task relationships
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import typer
from rich.console import Console


console = Console()


def generate_dag_html() -> str:
    """Generate HTML visualization of the DAG"""
    dag_file = Path("logs/dag.jsonl")

    if not dag_file.exists():
        return "<html><body><h1>No tasks found</h1></body></html>"

    # Load tasks
    tasks = []
    with open(dag_file) as f:
        for line in f:
            tasks.append(json.loads(line))

    # Build graph data
    nodes = []
    edges = []

    for task in tasks:
        # Create node
        status_color = {
            "completed": "#4CAF50",
            "failed": "#f44336",
            "running": "#FFC107",
            "created": "#2196F3",
        }.get(task.get("status", "unknown"), "#9E9E9E")

        nodes.append(
            {
                "id": task["task_id"],
                "label": f"{task['task_id'][:8]}\n{task['description'][:30]}",
                "color": status_color,
                "title": f"<b>{task['description']}</b><br>"
                f"Status: {task.get('status', 'unknown')}<br>"
                f"Time: {task.get('timestamp', 'N/A')}<br>"
                f"Async: {task.get('async', False)}",
            }
        )

        # Create edge if has parent
        if task.get("parent_id"):
            edges.append({"from": task["parent_id"], "to": task["task_id"], "arrows": "to"})

    # Generate HTML with vis.js
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Task DAG Visualization</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}

        #header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            margin: 0;
            color: #333;
            font-size: 28px;
        }}

        .stats {{
            margin-top: 10px;
            color: #666;
        }}

        .stat {{
            display: inline-block;
            margin-right: 30px;
            padding: 5px 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }}

        #network {{
            width: 100%;
            height: calc(100vh - 120px);
            background: white;
            border-top: 1px solid #ddd;
        }}

        .legend {{
            position: absolute;
            top: 140px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .legend-item {{
            margin: 5px 0;
        }}

        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🔀 Task DAG Visualization</h1>
        <div class="stats">
            <span class="stat">📊 Total Tasks: {len(tasks)}</span>
            <span class="stat">✅ Completed: {len([t for t in tasks if t.get('status') == 'completed'])}</span>
            <span class="stat">🔄 Running: {len([t for t in tasks if t.get('status') == 'running'])}</span>
            <span class="stat">❌ Failed: {len([t for t in tasks if t.get('status') == 'failed'])}</span>
        </div>
    </div>

    <div id="network"></div>

    <div class="legend">
        <div style="font-weight: bold; margin-bottom: 10px;">Status:</div>
        <div class="legend-item">
            <span class="legend-color" style="background: #4CAF50;"></span>Completed
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #FFC107;"></span>Running
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #2196F3;"></span>Created
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #f44336;"></span>Failed
        </div>
    </div>

    <script type="text/javascript">
        // Create nodes and edges
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});

        // Create network
        var container = document.getElementById('network');
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    nodeSpacing: 150,
                    levelSeparation: 100
                }}
            }},
            physics: {{
                enabled: false
            }},
            nodes: {{
                shape: 'box',
                margin: 10,
                font: {{
                    size: 12,
                    color: 'white',
                    face: 'monospace'
                }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 2,
                color: {{
                    color: '#848484',
                    highlight: '#333333'
                }},
                smooth: {{
                    enabled: true,
                    type: 'cubicBezier'
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200
            }}
        }};

        var network = new vis.Network(container, data, options);

        // Add click handler
        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var taskId = params.nodes[0];
                console.log("Clicked task:", taskId);
                // Could add modal or details view here
            }}
        }});
    </script>
</body>
</html>"""

    return html


def serve_dag(port: int = 8080):
    """Serve DAG visualization on local web server"""
    import http.server
    import socketserver
    import webbrowser
    from functools import partial

    class DAGHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "/dag":
                html = generate_dag_html()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
            else:
                super().do_GET()

    Handler = DAGHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        console.print(f"[green]DAG visualization server running at http://localhost:{port}[/green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")

        # Open browser
        webbrowser.open(f"http://localhost:{port}")

        httpd.serve_forever()


def export_dag_html(output_file: Path):
    """Export DAG visualization to HTML file"""
    html = generate_dag_html()
    output_file.write_text(html)
    console.print(f"[green]DAG exported to {output_file}[/green]")


if __name__ == "__main__":
    app = typer.Typer()

    @app.command()
    def serve(port: int = 8080):
        """Serve DAG visualization"""
        serve_dag(port)

    @app.command()
    def export(output: Path = Path("dag.html")):
        """Export DAG to HTML file"""
        export_dag_html(output)

    app()
