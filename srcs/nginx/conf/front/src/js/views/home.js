import * as THREE from 'three';

export function home_title(){
    return("Home");
}

export function home_view() {
    // HTML structure with a placeholder for the Three.js scene
    const content = `
        <div id="three-container" style="width: 100%; height: 100%;"></div>
    `;

    return content;
}

let scene, camera, renderer, cube;

export function initThreeJS() {
    const container = document.getElementById('three-container');
    scene = new THREE.Scene(); // Declare scene here
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    renderer = new THREE.WebGLRenderer();
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    // Set styles to ensure the renderer takes full size of the container
    renderer.domElement.style.position = 'absolute';
    renderer.domElement.style.top = 0;
    renderer.domElement.style.left = 0;
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';

    // Create cube geometry and material
    const geometry = new THREE.BoxGeometry();
    const material = new THREE.MeshBasicMaterial({ color: 0xeeeeee });
    cube = new THREE.Mesh(geometry, material);
    scene.add(cube);

    // Position the cube
    camera.position.z = 5;

    // Function to update cube's rotation
    function animate() {
        requestAnimationFrame(animate);
        cube.rotation.x += 0.01;
        cube.rotation.y += 0.01;
        renderer.render(scene, camera);
    }

    // Start animation loop
    animate();

    // Handle window resize
    window.addEventListener('resize', () => {
        const width = container.clientWidth;
        const height = container.clientHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    });
}

export function transitionToFace(faceIndex, callback) {
    const targetRotation = {
        0: { x: 0, y: 0 },          // Front face
        1: { x: 0, y: Math.PI / 2 }, // Right face
        2: { x: 0, y: Math.PI },     // Back face
        3: { x: 0, y: -Math.PI / 2 },// Left face
        4: { x: Math.PI / 2, y: 0 }, // Top face
        5: { x: -Math.PI / 2, y: 0 } // Bottom face
    }[faceIndex];

    const duration = 1000; // duration of the animation in milliseconds
    const initialRotation = { x: cube.rotation.x, y: cube.rotation.y };
    const initialZoom = camera.position.z;
    const targetZoom = 2; // Zoom in value
    const startTime = performance.now();

    function animateTransition(time) {
        const elapsed = time - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Interpolate rotation
        cube.rotation.x = initialRotation.x + (targetRotation.x - initialRotation.x) * progress;
        cube.rotation.y = initialRotation.y + (targetRotation.y - initialRotation.y) * progress;

        // Interpolate zoom
        camera.position.z = initialZoom + (targetZoom - initialZoom) * progress;

        renderer.render(scene, camera);

        if (progress < 1)
            requestAnimationFrame(animateTransition);
    }

    requestAnimationFrame(animateTransition);
    return new Promise((resolve, reject) => {
        try {
            // Perform the animation
            // Call onComplete once the animation is done
            callback();
            resolve();
        } catch (error) {
            reject(error);
        }
    });
}