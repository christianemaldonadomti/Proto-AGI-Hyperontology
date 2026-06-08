<?php
// Aumentar memoria para procesar la ontología
ini_set('memory_limit', '512M'); 
$json_file = __DIR__ . '/ontologias/hiperontologia_final.json';

if (!file_exists($json_file)) {
    die("<h2 style='color:#ff4d4d; font-family:sans-serif;'>Error: No se encuentra $json_file</h2>");
}

$json_data = file_get_contents($json_file);
$data = json_decode($json_data, true);

// 1. Indexar nodos y contar hiperconexiones (Grados)
$nodos = [];
$grados = [];
foreach ($data['nodos'] as $n) {
    if (is_array($n)) {
        $id = $n['id'] ?? ($n['label'] ?? null);
        if ($id) {
            $nodos[$id] = $n;
            $grados[$id] = 0;
        }
    }
}

foreach ($data['hiperaristas'] as $e) {
    $src = $e['source'] ?? ($e[0] ?? null);
    $tgt = $e['target'] ?? ($e[1] ?? null);
    if ($src && isset($grados[$src])) $grados[$src]++;
    if ($tgt && isset($grados[$tgt])) $grados[$tgt]++;
}

arsort($grados);
$top_hubs = array_slice($grados, 0, 30, true); 

// 2. Controladores de Estado (Nodo Central y Límite de Renderizado)
$center_id = $_GET['node'] ?? array_key_first($top_hubs);
$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 60;
if ($limit < 10) $limit = 10;
if ($limit > 300) $limit = 300; // Protegemos el navegador limitando a 300 max

// 3. Extraer subgrafo local y datos para el Panel Derecho
$graph_nodes = [];
$graph_links = [];
$added_nodes = [];
$tree_connections = []; // Almacenará el texto para el panel derecho

$addNode = function($id, $label, $group, $desc = '') use (&$graph_nodes, &$added_nodes) {
    if (!isset($added_nodes[$id])) {
        $graph_nodes[] = [
            'id' => (string)$id, 
            'name' => $label, 
            'group' => $group,
            'desc' => $desc
        ];
        $added_nodes[$id] = true;
    }
};

// Añadir el nodo central
$addNode($center_id, $nodos[$center_id]['label'] ?? $center_id, 'center', $nodos[$center_id]['desc'] ?? '');

$connection_count = 0;

foreach ($data['hiperaristas'] as $e) {
    $src = $e['source'] ?? ($e[0] ?? null);
    $tgt = $e['target'] ?? ($e[1] ?? null);
    $lbl = $e['label'] ?? 'relacion';

    if ($src === $center_id || $tgt === $center_id) {
        $other_id = ($src === $center_id) ? $tgt : $src;
        $other_label = $nodos[$other_id]['label'] ?? $other_id;
        $other_desc = $nodos[$other_id]['desc'] ?? '';
        
        // Guardar para el Panel Derecho (Independiente del límite gráfico)
        $tree_connections[] = [
            'direction' => ($src === $center_id) ? 'apunta a' : 'recibe de',
            'label' => $lbl,
            'target_id' => $other_id,
            'target_name' => $other_label
        ];

        // Límite de renderizado para evitar colapso WebGL
        if ($connection_count < $limit) {
            $addNode($other_id, $other_label, 'concept', $other_desc);
            
            // Reificación
            $rel_id = 'rel_' . uniqid();
            $addNode($rel_id, $lbl, 'relation', 'Conecta ' . $src . ' con ' . $tgt);
            
            $graph_links[] = ['source' => (string)$src, 'target' => $rel_id];
            $graph_links[] = ['source' => $rel_id, 'target' => (string)$tgt];
            
            $connection_count++;
        }
    }
}

$graphDataJSON = json_encode(['nodes' => $graph_nodes, 'links' => $graph_links]);
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Hiperontología - Reader Math</title>
    <style>
        /* SCROLLBARS DISCRETOS Y ELEGANTES */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #4facfe; }

        body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; overflow: hidden; display: flex; width: 100vw; height: 100vh; }
        
        /* PANELES LATERALES (SIDEBARS) */
        .sidebar {
            width: 340px; background: rgba(30, 41, 59, 0.95); backdrop-filter: blur(10px);
            height: 100%; display: flex; flex-direction: column; z-index: 20; position: absolute; top: 0;
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .sidebar-header { padding: 20px; background: rgba(15, 23, 42, 0.9); border-bottom: 1px solid #334155; }
        .sidebar-header h2 { margin: 0; font-size: 1.1em; color: #f8fafc; }
        .sidebar-content { flex: 1; overflow-y: auto; padding-bottom: 20px; }

        /* Panel Izquierdo (Hubs) */
        #left-sidebar { left: 0; border-right: 1px solid #334155; }
        #left-sidebar.collapsed { transform: translateX(-100%); }
        #left-sidebar .sidebar-header h2 { color: #38bdf8; }

        /* Panel Derecho (Árbol del Concepto) */
        #right-sidebar { right: 0; border-left: 1px solid #334155; }
        #right-sidebar.collapsed { transform: translateX(100%); }
        #right-sidebar .sidebar-header h2 { color: #f87171; }

        /* PESTAÑAS COLAPSABLES */
        .toggle-btn {
            position: absolute; top: 50%; transform: translateY(-50%); width: 24px; height: 60px;
            background: #334155; color: white; display: flex; align-items: center; justify-content: center;
            cursor: pointer; font-size: 14px; transition: background 0.2s; box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }
        .toggle-btn:hover { background: #475569; }
        #left-sidebar .toggle-btn { right: -24px; border-radius: 0 6px 6px 0; }
        #right-sidebar .toggle-btn { left: -24px; border-radius: 6px 0 0 6px; }

        /* ACORDEÓN FINO PARA HUBS */
        details.hub-item { border-bottom: 1px solid #1e293b; transition: background 0.2s; }
        details.hub-item:hover { background: #334155; }
        summary { cursor: pointer; padding: 12px 20px; font-size: 0.9em; font-weight: 500; color: #e2e8f0; outline: none; list-style: none; display: flex; justify-content: space-between; align-items: center; }
        summary::-webkit-details-marker { display: none; }
        .hub-count { font-size: 0.75em; color: #94a3b8; background: #0f172a; padding: 3px 8px; border-radius: 12px; }
        .hub-desc { font-size: 0.8em; color: #94a3b8; margin: 0 20px 15px 20px; line-height: 1.5; border-left: 2px solid #38bdf8; padding-left: 10px; }
        .btn-explore { display: inline-block; margin-top: 8px; color: #38bdf8; text-decoration: none; font-weight: bold; }
        .btn-explore:hover { text-decoration: underline; }

        /* LISTA DEL ÁRBOL SEMÁNTICO (Panel Derecho) */
        .tree-list { list-style: none; padding: 0; margin: 0; }
        .tree-item { padding: 12px 20px; border-bottom: 1px solid #1e293b; }
        .tree-lbl { color: #a855f7; background: rgba(168,85,247,0.15); padding: 2px 6px; border-radius: 4px; font-size: 0.75em; display: inline-block; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px;}
        .tree-tgt { display: block; color: #f8fafc; text-decoration: none; font-size: 0.9em; font-weight: 500; }
        .tree-tgt:hover { color: #f87171; }

        /* CONTROLES CENTRALES Y LIENZO */
        #main-view { flex: 1; position: relative; height: 100%; overflow: hidden; }
        .graph-wrapper { width: 100%; height: 100%; position: absolute; top: 0; left: 0; outline: none; }
        
        #ui-layer {
            position: absolute; top: 20px; left: 50%; transform: translateX(-50%); z-index: 10;
            background: rgba(15, 23, 42, 0.85); padding: 15px 25px; border-radius: 8px; border: 1px solid #334155;
            backdrop-filter: blur(4px); display: flex; flex-direction: column; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        
        /* SLIDER DE RENDIMIENTO */
        .slider-container { width: 100%; text-align: center; margin-bottom: 12px; }
        .slider-container label { font-size: 0.8em; color: #94a3b8; display: block; margin-bottom: 5px; }
        input[type=range] { width: 100%; cursor: pointer; accent-color: #38bdf8; }

        .controls button {
            background: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 6px 12px;
            cursor: pointer; border-radius: 4px; margin: 0 2px; font-weight: 600; transition: all 0.2s; font-size: 0.85em;
        }
        .controls button:hover { background: #334155; color: white; }
        .controls button.active { background: #38bdf8; color: #0f172a; border-color: #38bdf8; }
        
        #tooltip { position: absolute; background: rgba(15, 23, 42, 0.95); color: #f8fafc; padding: 12px; border-radius: 6px; pointer-events: none; display: none; z-index: 30; max-width: 250px; font-size: 0.85em; border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    </style>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js"></script>
    <script src="https://unpkg.com/force-graph@1.43.3/dist/force-graph.min.js"></script>
</head>
<body>

<div id="left-sidebar" class="sidebar">
    <div class="sidebar-header">
        <h2>Top Conceptos</h2>
        <p style="font-size: 0.75em; color: #94a3b8; margin-top: 5px;">Centros neurálgicos de la ontología</p>
    </div>
    <div class="sidebar-content">
        <?php foreach ($top_hubs as $id => $count): ?>
            <details class="hub-item">
                <summary>
                    <span class="hub-name"><?= htmlspecialchars($nodos[$id]['label'] ?? $id) ?></span>
                    <span class="hub-count"><?= $count ?> conn</span>
                </summary>
                <div class="hub-desc">
                    <?= htmlspecialchars($nodos[$id]['desc'] ?? 'Sin descripción.') ?>
                    <br>
                    <a class="btn-explore" href="reader-math.php?node=<?= urlencode($id) ?>&limit=<?= $limit ?>">Navegar aquí ⭢</a>
                </div>
            </details>
        <?php endforeach; ?>
    </div>
    <div class="toggle-btn" onclick="toggleSidebar('left-sidebar')" title="Ocultar/Mostrar Panel">⟨</div>
</div>

<div id="right-sidebar" class="sidebar">
    <div class="sidebar-header">
        <h2>Estructura Semántica</h2>
        <p style="font-size: 0.75em; color: #94a3b8; margin-top: 5px;">Relaciones del concepto actual</p>
    </div>
    <div class="sidebar-content">
        <div style="padding: 15px 20px;">
            <h3 style="color:#f87171; margin: 0 0 10px 0;"><?= htmlspecialchars($nodos[$center_id]['label'] ?? $center_id) ?></h3>
            <p style="font-size:0.85em; color:#cbd5e1; line-height:1.5; margin:0;"><?= htmlspecialchars($nodos[$center_id]['desc'] ?? 'Sin descripción') ?></p>
        </div>
        <hr style="border:0; border-top:1px solid #334155; margin:0;">
        <ul class="tree-list">
            <?php foreach($tree_connections as $conn): ?>
                <li class="tree-item">
                    <span class="tree-lbl"><?= htmlspecialchars($conn['label']) ?></span>
                    <a href="reader-math.php?node=<?= urlencode($conn['target_id']) ?>&limit=<?= $limit ?>" class="tree-tgt">
                        <?= ($conn['direction'] == 'recibe de' ? '⭠ ' : '⭢ ') . htmlspecialchars($conn['target_name']) ?>
                    </a>
                </li>
            <?php endforeach; ?>
        </ul>
    </div>
    <div class="toggle-btn" onclick="toggleSidebar('right-sidebar')" title="Ocultar/Mostrar Panel">⟩</div>
</div>

<div id="main-view">
    <div id="ui-layer">
        <div class="slider-container">
            <label for="node-limit">Densidad de renderizado: <span id="limit-val"><?= $limit ?></span> nodos</label>
            <input type="range" id="node-limit" min="10" max="300" step="10" value="<?= $limit ?>" 
                   oninput="document.getElementById('limit-val').innerText = this.value" 
                   onchange="updateLimit(this.value)">
        </div>
        
        <div class="controls">
            <button type="button" id="btn-2d" onclick="switchTo2D()">Vista 2D (Reificada)</button>
            <button type="button" id="btn-3d" onclick="switchTo3D()">Vista 3D (Polígonos)</button>
        </div>
    </div>

    <div id="tooltip"></div>
    <div id="graph-2d" class="graph-wrapper" style="display: block;"></div>
    <div id="graph-3d" class="graph-wrapper" style="display: none;"></div>
</div>

<script>
    const graphData = <?= $graphDataJSON ?>;
    const tooltip = document.getElementById('tooltip');
    
    let graph2DInstance = null;
    let graph3DInstance = null;

    const colorMap = { 'center': '#f87171', 'concept': '#38bdf8', 'relation': '#a855f7' };

    // Funciones de UI
    function toggleSidebar(id) {
        document.getElementById(id).classList.toggle('collapsed');
    }

    function updateLimit(val) {
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('limit', val);
        window.location.search = urlParams.toString();
    }

    function handleNodeClick(node) {
        if (node.group === 'concept' || node.group === 'center') {
            window.location.href = 'reader-math.php?node=' + encodeURIComponent(node.id) + '&limit=<?= $limit ?>';
        }
    }

    function highlightButton(activeId) {
        document.getElementById('btn-3d').classList.remove('active');
        document.getElementById('btn-2d').classList.remove('active');
        document.getElementById(activeId).classList.add('active');
    }

    function switchTo2D() {
        highlightButton('btn-2d');
        document.getElementById('graph-3d').style.display = 'none';
        document.getElementById('graph-2d').style.display = 'block';
        if (!graph2DInstance) init2D();
    }

    function switchTo3D() {
        highlightButton('btn-3d');
        document.getElementById('graph-2d').style.display = 'none';
        document.getElementById('graph-3d').style.display = 'block';
        if (!graph3DInstance) init3D();
    }

    // Inicializar Grafo 3D
    function init3D() {
        const container = document.getElementById('graph-3d');
        graph3DInstance = ForceGraph3D()(container)
            .graphData(graphData)
            .nodeLabel('name')
            .linkWidth(1.2)
            .linkOpacity(0.3)
            .nodeThreeObject(node => {
                if (node.group === 'relation') {
                    const geometry = new THREE.TetrahedronGeometry(4);
                    const material = new THREE.MeshLambertMaterial({ color: colorMap[node.group], transparent: true, opacity: 0.7 });
                    return new THREE.Mesh(geometry, material);
                } else {
                    const size = node.group === 'center' ? 8 : 4;
                    const geometry = new THREE.SphereGeometry(size);
                    const material = new THREE.MeshLambertMaterial({ color: colorMap[node.group] });
                    return new THREE.Mesh(geometry, material);
                }
            })
            .onNodeHover(node => container.style.cursor = node ? 'pointer' : null)
            .onNodeClick(handleNodeClick);
            
        const scene = graph3DInstance.scene();
        scene.add(new THREE.AmbientLight(0x888888));
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        scene.add(directionalLight);
    }

    // Inicializar Grafo 2D
    function init2D() {
        const container = document.getElementById('graph-2d');
        graph2DInstance = ForceGraph()(container)
            .graphData(graphData)
            .nodeCanvasObject((node, ctx, globalScale) => {
                const label = node.name;
                const isCenter = node.group === 'center';
                const isRelation = node.group === 'relation';
                
                ctx.beginPath();
                if (isRelation) {
                    const size = 5;
                    ctx.moveTo(node.x, node.y - size);
                    ctx.lineTo(node.x + size, node.y);
                    ctx.lineTo(node.x, node.y + size);
                    ctx.lineTo(node.x - size, node.y);
                    ctx.fillStyle = colorMap[node.group];
                } else {
                    const r = isCenter ? 8 : 5;
                    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                    ctx.fillStyle = colorMap[node.group];
                }
                ctx.fill();

                if (globalScale >= 1.5 || isCenter) {
                    const fontSize = isCenter ? 12/globalScale : (isRelation ? 8/globalScale : 10/globalScale);
                    ctx.font = `${fontSize}px Sans-Serif`;
                    const textWidth = ctx.measureText(label).width;
                    const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); 
                    
                    ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
                    ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + 7, bckgDimensions[0], bckgDimensions[1]);
                    
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = isRelation ? '#d8b4fe' : '#f8fafc';
                    ctx.fillText(label, node.x, node.y + 7 + (bckgDimensions[1]/2));
                }
            })
            .linkDirectionalParticles(2)
            .linkDirectionalParticleSpeed(0.006)
            .linkDirectionalParticleWidth(2)
            .linkColor(() => '#334155')
            .onNodeHover(node => {
                container.style.cursor = node ? 'pointer' : null;
                if (node) {
                    tooltip.style.display = 'block';
                    tooltip.innerHTML = `<strong>${node.name}</strong><br><span style="color:#94a3b8; font-size: 0.9em;">${node.desc || (node.group === 'relation' ? 'Polígono de Relación Lógica' : '')}</span>`;
                } else {
                    tooltip.style.display = 'none';
                }
            })
            .onNodeClick(handleNodeClick);

        container.addEventListener('mousemove', (e) => {
            if (tooltip.style.display === 'block') {
                const rect = document.getElementById('main-view').getBoundingClientRect();
                tooltip.style.left = (e.clientX - rect.left + 15) + 'px';
                tooltip.style.top = (e.clientY - rect.top + 15) + 'px';
            }
        });
    }

    switchTo2D();
</script>
</body>
</html>