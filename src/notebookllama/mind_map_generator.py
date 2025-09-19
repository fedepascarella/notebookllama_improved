"""
Mind Map Generator - Creates interactive HTML mind maps from document topics
Senior-level implementation with proper graph structure and visualization
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid
import colorsys

logger = logging.getLogger(__name__)


@dataclass
class MindMapNode:
    """Represents a node in the mind map"""
    id: str
    label: str
    level: int
    parent_id: Optional[str] = None
    color: Optional[str] = None
    size: int = 20
    children: List[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class MindMapGenerator:
    """
    Generates interactive HTML mind maps using vis.js network
    Creates hierarchical structures from document topics and content
    """

    def __init__(self):
        self.node_colors = self._generate_color_palette()

    def generate_mind_map(
        self,
        title: str,
        topics: List[str],
        key_points: List[str],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate complete HTML mind map

        Args:
            title: Document title (root node)
            topics: Main topics (level 1 nodes)
            key_points: Key points (level 2 nodes)
            additional_data: Optional metadata for enhanced visualization

        Returns:
            Complete HTML string with embedded vis.js mind map
        """
        try:
            logger.info(f"Generating mind map for '{title}' with {len(topics)} topics")

            # Create hierarchical structure
            nodes, edges = self._create_graph_structure(title, topics, key_points)

            # Generate HTML with embedded JavaScript
            html_content = self._generate_html(nodes, edges, title)

            logger.info("Mind map generated successfully")
            return html_content

        except Exception as e:
            logger.error(f"Mind map generation failed: {e}")
            return self._create_fallback_mind_map(title, topics)

    def _create_graph_structure(
        self,
        title: str,
        topics: List[str],
        key_points: List[str]
    ) -> tuple[List[Dict], List[Dict]]:
        """Create nodes and edges for the mind map graph"""

        nodes = []
        edges = []

        # Root node (document title)
        root_id = "root"
        nodes.append({
            "id": root_id,
            "label": self._truncate_text(title, 30),
            "color": {"background": "#4CAF50", "border": "#45a049"},
            "font": {"size": 16, "color": "white"},
            "shape": "ellipse",
            "size": 30,
            "title": title  # Tooltip
        })

        # Topic nodes (level 1)
        topic_ids = []
        for i, topic in enumerate(topics):
            if not topic.strip():
                continue

            topic_id = f"topic_{i}"
            topic_ids.append(topic_id)

            color = self.node_colors[i % len(self.node_colors)]
            nodes.append({
                "id": topic_id,
                "label": self._truncate_text(topic, 20),
                "color": {"background": color, "border": self._darken_color(color)},
                "font": {"size": 14},
                "shape": "box",
                "size": 25,
                "title": topic
            })

            # Edge from root to topic
            edges.append({
                "from": root_id,
                "to": topic_id,
                "color": {"color": "#999999"},
                "width": 2
            })

        # Key point nodes (level 2) - distribute among topics
        points_per_topic = max(1, len(key_points) // max(1, len(topic_ids)))

        for i, point in enumerate(key_points):
            if not point.strip():
                continue

            point_id = f"point_{i}"
            topic_index = min(i // points_per_topic, len(topic_ids) - 1)
            parent_topic = topic_ids[topic_index] if topic_ids else root_id

            color = self._lighten_color(self.node_colors[topic_index % len(self.node_colors)])
            nodes.append({
                "id": point_id,
                "label": self._truncate_text(point, 25),
                "color": {"background": color, "border": self._darken_color(color)},
                "font": {"size": 12},
                "shape": "circle",
                "size": 20,
                "title": point
            })

            # Edge from topic to key point
            edges.append({
                "from": parent_topic,
                "to": point_id,
                "color": {"color": "#cccccc"},
                "width": 1
            })

        return nodes, edges

    def _generate_html(self, nodes: List[Dict], edges: List[Dict], title: str) -> str:
        """Generate complete HTML with vis.js mind map"""

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mind Map: {title}</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}

        #mindmap {{
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .header {{
            text-align: center;
            margin-bottom: 20px;
            color: #333;
        }}

        .controls {{
            text-align: center;
            margin-bottom: 15px;
        }}

        .control-btn {{
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}

        .control-btn:hover {{
            background-color: #45a049;
        }}

        .info {{
            text-align: center;
            margin-top: 10px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2>📊 Mind Map: {title}</h2>
    </div>

    <div class="controls">
        <button class="control-btn" onclick="fitNetwork()">🔍 Fit View</button>
        <button class="control-btn" onclick="togglePhysics()">⚡ Toggle Physics</button>
        <button class="control-btn" onclick="resetView()">🔄 Reset</button>
    </div>

    <div id="mindmap"></div>

    <div class="info">
        💡 Click and drag nodes • Scroll to zoom • Hover for details
    </div>

    <script type="text/javascript">
        // Network data
        var nodes = new vis.DataSet({json.dumps(nodes, indent=2)});
        var edges = new vis.DataSet({json.dumps(edges, indent=2)});
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        // Configuration options
        var options = {{
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 200,
                    treeSpacing: 200
                }}
            }},
            physics: {{
                enabled: true,
                hierarchicalRepulsion: {{
                    centralGravity: 0.0,
                    springLength: 100,
                    springConstant: 0.01,
                    nodeDistance: 120,
                    damping: 0.09
                }},
                maxVelocity: 50,
                minVelocity: 0.1,
                solver: 'hierarchicalRepulsion',
                stabilization: {{
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 25
                }}
            }},
            interaction: {{
                dragNodes: true,
                dragView: true,
                zoomView: true,
                selectConnectedEdges: false
            }},
            nodes: {{
                borderWidth: 2,
                shadow: {{
                    enabled: true,
                    color: 'rgba(0,0,0,0.2)',
                    size: 10,
                    x: 2,
                    y: 2
                }},
                font: {{
                    color: '#333333',
                    strokeWidth: 0,
                    strokeColor: '#ffffff'
                }}
            }},
            edges: {{
                smooth: {{
                    enabled: true,
                    type: 'continuous',
                    roundness: 0.5
                }},
                shadow: {{
                    enabled: true,
                    color: 'rgba(0,0,0,0.1)',
                    size: 5,
                    x: 2,
                    y: 2
                }}
            }}
        }};

        // Create network
        var container = document.getElementById('mindmap');
        var network = new vis.Network(container, data, options);

        // Control functions
        function fitNetwork() {{
            network.fit({{
                animation: {{
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
        }}

        function togglePhysics() {{
            var enabled = network.physics.physicsEnabled;
            network.setOptions({{physics: {{enabled: !enabled}}}});
        }}

        function resetView() {{
            network.setData(data);
            fitNetwork();
        }}

        // Event handlers
        network.on('selectNode', function(properties) {{
            var nodeId = properties.nodes[0];
            var node = nodes.get(nodeId);
            if (node && node.title) {{
                console.log('Selected:', node.title);
            }}
        }});

        network.on('stabilizationIterationsDone', function() {{
            network.setOptions({{physics: false}});
        }});

        // Initial fit
        setTimeout(function() {{
            fitNetwork();
        }}, 1000);
    </script>
</body>
</html>"""

    def _generate_color_palette(self) -> List[str]:
        """Generate a visually appealing color palette"""
        colors = []
        num_colors = 12

        for i in range(num_colors):
            hue = i / num_colors
            saturation = 0.7
            lightness = 0.6
            rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(hex_color)

        return colors

    def _lighten_color(self, hex_color: str, factor: float = 0.3) -> str:
        """Lighten a hex color"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')

            # Convert to RGB
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            # Lighten
            lightened = tuple(
                min(255, int(c + (255 - c) * factor)) for c in rgb
            )

            # Convert back to hex
            return '#{:02x}{:02x}{:02x}'.format(*lightened)

        except:
            return "#e0e0e0"  # Fallback light gray

    def _darken_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Darken a hex color"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')

            # Convert to RGB
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            # Darken
            darkened = tuple(int(c * (1 - factor)) for c in rgb)

            # Convert back to hex
            return '#{:02x}{:02x}{:02x}'.format(*darkened)

        except:
            return "#666666"  # Fallback dark gray

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text for display in nodes"""
        if len(text) <= max_length:
            return text

        # Try to break at word boundary
        if ' ' in text[:max_length]:
            truncated = text[:max_length].rsplit(' ', 1)[0]
        else:
            truncated = text[:max_length-3]

        return truncated + "..."

    def _create_fallback_mind_map(self, title: str, topics: List[str]) -> str:
        """Create a simple fallback mind map when generation fails"""
        logger.warning("Creating fallback mind map")

        simple_nodes = [
            {
                "id": "root",
                "label": self._truncate_text(title, 30),
                "color": {"background": "#4CAF50", "border": "#45a049"},
                "font": {"size": 16, "color": "white"},
                "shape": "ellipse",
                "size": 30
            }
        ]

        simple_edges = []

        # Add basic topic nodes
        for i, topic in enumerate(topics[:6]):  # Limit to 6 topics
            if topic.strip():
                topic_id = f"topic_{i}"
                simple_nodes.append({
                    "id": topic_id,
                    "label": self._truncate_text(topic, 20),
                    "color": {"background": "#2196F3", "border": "#1976D2"},
                    "font": {"size": 14},
                    "shape": "box",
                    "size": 25
                })

                simple_edges.append({
                    "from": "root",
                    "to": topic_id,
                    "color": {"color": "#999999"},
                    "width": 2
                })

        return self._generate_html(simple_nodes, simple_edges, title)


# Factory function
def create_mind_map_generator() -> MindMapGenerator:
    """Create mind map generator instance"""
    return MindMapGenerator()