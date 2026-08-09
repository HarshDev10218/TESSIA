class ForceGraph {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');

    this.nodes = [];
    this.edges = [];
    this.nodeMap = new Map();

    // Canvas View State (Pan & Zoom)
    this.scale = 1.0;
    this.panX = 0;
    this.panY = 0;

    // Interaction states
    this.isDragging = false;
    this.draggedNode = null;
    this.hoveredNode = null;
    this.selectedNode = null;
    this.pathNodes = new Set();
    this.pathEdges = new Set();
    this.shiftSelectedNodes = [];

    this.physicsEnabled = true;
    this.listeners = {};

    this.initCanvas();
    this.bindEvents();
    this.animate();
  }

  initCanvas() {
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    const parent = this.canvas.parentElement;
    this.canvas.width = parent.clientWidth;
    this.canvas.height = parent.clientHeight;
    if (this.nodes.length === 0) {
      this.panX = this.canvas.width / 2;
      this.panY = this.canvas.height / 2;
    }
  }

  setData(rawNodes, rawEdges) {
    this.nodeMap.clear();
    const width = this.canvas.width || 800;
    const height = this.canvas.height || 600;

    this.nodes = rawNodes.map(n => {
      const radius = Math.min(18, Math.max(5, 4 + n.total_degree * 2));
      const node = {
        ...n,
        x: (Math.random() - 0.5) * (width * 0.6),
        y: (Math.random() - 0.5) * (height * 0.6),
        vx: 0,
        vy: 0,
        radius: radius,
        color: n.is_virtual ? '#64748b' : (n.extension === '.md' ? '#00f0ff' : '#00ffaa')
      };
      this.nodeMap.set(n.id, node);
      return node;
    });

    this.edges = rawEdges.map(e => ({
      source: this.nodeMap.get(e.source),
      target: this.nodeMap.get(e.target)
    })).filter(e => e.source && e.target);

    this.centerGraph();
  }

  centerGraph() {
    this.panX = this.canvas.width / 2;
    this.panY = this.canvas.height / 2;
  }

  // Force Layout simulation step using Spatial Grid & Cutoff
  updatePhysics() {
    if (!this.physicsEnabled) return;

    const repulsionStrength = 3500;
    const distanceCutoff = 250;
    const springLength = 70;
    const springStrength = 0.04;
    const centerGravity = 0.01;
    const damping = 0.82;

    // 1. Repulsion force with cutoff
    for (let i = 0; i < this.nodes.length; i++) {
      const nodeA = this.nodes[i];
      for (let j = i + 1; j < this.nodes.length; j++) {
        const nodeB = this.nodes[j];
        const dx = nodeB.x - nodeA.x;
        const dy = nodeB.y - nodeA.y;
        const distSq = dx * dx + dy * dy + 0.1;
        const dist = Math.sqrt(distSq);

        if (dist < distanceCutoff) {
          const force = repulsionStrength / distSq;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          nodeA.vx -= fx;
          nodeA.vy -= fy;
          nodeB.vx += fx;
          nodeB.vy += fy;
        }
      }
    }

    // 2. Spring forces along edges
    for (const edge of this.edges) {
      const dx = edge.target.x - edge.source.x;
      const dy = edge.target.y - edge.source.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - springLength) * springStrength;

      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      edge.source.vx += fx;
      edge.source.vy += fy;
      edge.target.vx -= fx;
      edge.target.vy -= fy;
    }

    // 3. Apply velocity, damping & center gravity
    for (const node of this.nodes) {
      if (node === this.draggedNode) continue;

      node.vx -= node.x * centerGravity;
      node.vy -= node.y * centerGravity;

      node.vx *= damping;
      node.vy *= damping;

      node.x += node.vx;
      node.y += node.vy;
    }
  }

  // Render Loop
  render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    this.ctx.save();
    this.ctx.translate(this.panX, this.panY);
    this.ctx.scale(this.scale, this.scale);

    const isHighlighting = this.hoveredNode || this.selectedNode || this.pathNodes.size > 0;

    // 1. Draw Edges
    for (const edge of this.edges) {
      const isPathEdge = this.pathEdges.has(edge);
      const isConnectedToHover = this.hoveredNode && (edge.source === this.hoveredNode || edge.target === this.hoveredNode);

      let alpha = 0.15;
      let strokeColor = 'rgba(255, 255, 255, 0.12)';
      let lineWidth = 1;

      if (isPathEdge) {
        alpha = 1.0;
        strokeColor = '#00ffaa';
        lineWidth = 3;
      } else if (isConnectedToHover) {
        alpha = 0.8;
        strokeColor = '#00f0ff';
        lineWidth = 2;
      } else if (isHighlighting) {
        alpha = 0.05;
      }

      this.ctx.beginPath();
      this.ctx.moveTo(edge.source.x, edge.source.y);
      this.ctx.lineTo(edge.target.x, edge.target.y);
      this.ctx.strokeStyle = strokeColor;
      this.ctx.globalAlpha = alpha;
      this.ctx.lineWidth = lineWidth;
      this.ctx.stroke();
    }
    this.ctx.globalAlpha = 1.0;

    // 2. Draw Nodes
    for (const node of this.nodes) {
      const isSelected = this.selectedNode === node;
      const isHovered = this.hoveredNode === node;
      const isPathNode = this.pathNodes.has(node);
      const isConnectedToHover = this.hoveredNode && this.isNeighbor(this.hoveredNode, node);

      let alpha = 1.0;
      if (isHighlighting && !isSelected && !isHovered && !isPathNode && !isConnectedToHover) {
        alpha = 0.1; // Fade unrelated nodes to 10%
      }

      this.ctx.save();
      this.ctx.globalAlpha = alpha;

      // Glow ring
      if (isSelected || isHovered || isPathNode) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + 6, 0, Math.PI * 2);
        this.ctx.fillStyle = isPathNode ? 'rgba(0, 255, 170, 0.3)' : 'rgba(0, 240, 255, 0.3)';
        this.ctx.fill();
      }

      // Core Node
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = node.color;
      this.ctx.fill();

      this.ctx.restore();
    }

    // 3. Draw Labels with Collision Prevention
    this.drawLabelsWithCollisionPrevention();

    this.ctx.restore();
  }

  // Label Collision Prevention Algorithm
  drawLabelsWithCollisionPrevention() {
    // Sort nodes descending by total degree (hubs drawn first)
    const sortedNodes = [...this.nodes].sort((a, b) => b.total_degree - a.total_degree);
    const drawnBoxes = [];

    this.ctx.font = '11px sans-serif';
    this.ctx.textAlign = 'center';

    for (const node of sortedNodes) {
      const isHovered = this.hoveredNode === node;
      const isSelected = this.selectedNode === node;
      const isPathNode = this.pathNodes.has(node);

      // Always draw labels for hovered, selected, or high-hub nodes
      const text = node.title;
      const textWidth = this.ctx.measureText(text).width;
      const box = {
        x: node.x - textWidth / 2 - 4,
        y: node.y + node.radius + 4,
        width: textWidth + 8,
        height: 14
      };

      let hasCollision = false;
      if (!isHovered && !isSelected && !isPathNode) {
        for (const existingBox of drawnBoxes) {
          if (this.boxesOverlap(box, existingBox)) {
            hasCollision = true;
            break;
          }
        }
      }

      if (!hasCollision || isHovered || isSelected || isPathNode) {
        drawnBoxes.push(box);
        this.ctx.fillStyle = (isSelected || isHovered) ? '#00f0ff' : '#cbd5e1';
        this.ctx.fillText(text, node.x, node.y + node.radius + 14);
      }
    }
  }

  boxesOverlap(a, b) {
    return !(a.x + a.width < b.x || b.x + b.width < a.x || a.y + a.height < b.y || b.y + b.height < a.y);
  }

  isNeighbor(a, b) {
    return this.edges.some(e => (e.source === a && e.target === b) || (e.source === b && e.target === a));
  }

  // Shortest Path Dijkstra BFS
  findShortestPath(startNode, endNode) {
    if (!startNode || !endNode) return;

    const queue = [[startNode]];
    const visited = new Set([startNode]);

    while (queue.length > 0) {
      const path = queue.shift();
      const current = path[path.length - 1];

      if (current === endNode) {
        this.highlightPath(path);
        return path;
      }

      const neighbors = this.edges
        .filter(e => e.source === current || e.target === current)
        .map(e => e.source === current ? e.target : e.source);

      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          queue.push([...path, neighbor]);
        }
      }
    }
    return null;
  }

  highlightPath(path) {
    this.pathNodes = new Set(path);
    this.pathEdges = new Set();

    for (let i = 0; i < path.length - 1; i++) {
      const u = path[i];
      const v = path[i + 1];
      const edge = this.edges.find(e => (e.source === u && e.target === v) || (e.source === v && e.target === u));
      if (edge) this.pathEdges.add(edge);
    }
  }

  clearPath() {
    this.pathNodes.clear();
    this.pathEdges.clear();
    this.shiftSelectedNodes = [];
  }

  animate() {
    this.updatePhysics();
    this.render();
    requestAnimationFrame(() => this.animate());
  }

  bindEvents() {
    let lastX = 0, lastY = 0;

    this.canvas.addEventListener('mousedown', (e) => {
      const pos = this.getCanvasPos(e);
      const clickedNode = this.getNodeAt(pos.x, pos.y);

      if (clickedNode) {
        if (e.shiftKey) {
          // Shift-click for shortest path calculation
          this.shiftSelectedNodes.push(clickedNode);
          if (this.shiftSelectedNodes.length === 2) {
            this.findShortestPath(this.shiftSelectedNodes[0], this.shiftSelectedNodes[1]);
            if (this.listeners['shortestPath']) {
              this.listeners['shortestPath'](this.shiftSelectedNodes[0], this.shiftSelectedNodes[1]);
            }
          }
        } else {
          this.clearPath();
          this.selectedNode = clickedNode;
          this.draggedNode = clickedNode;
          if (this.listeners['nodeClick']) this.listeners['nodeClick'](clickedNode);
        }
      } else {
        this.isDragging = true;
        this.clearPath();
      }
      lastX = e.clientX;
      lastY = e.clientY;
    });

    window.addEventListener('mousemove', (e) => {
      const pos = this.getCanvasPos(e);

      if (this.draggedNode) {
        this.draggedNode.x = pos.x;
        this.draggedNode.y = pos.y;
      } else if (this.isDragging) {
        this.panX += e.clientX - lastX;
        this.panY += e.clientY - lastY;
        lastX = e.clientX;
        lastY = e.clientY;
      } else {
        this.hoveredNode = this.getNodeAt(pos.x, pos.y);
      }
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
      this.draggedNode = null;
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      this.scale *= zoomFactor;
      this.scale = Math.min(Math.max(0.2, this.scale), 4.0);
    });
  }

  getCanvasPos(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left - this.panX) / this.scale,
      y: (e.clientY - rect.top - this.panY) / this.scale
    };
  }

  getNodeAt(x, y) {
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const node = this.nodes[i];
      const dx = node.x - x;
      const dy = node.y - y;
      if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 4) {
        return node;
      }
    }
    return null;
  }

  on(event, cb) {
    this.listeners[event] = cb;
  }
}