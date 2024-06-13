// import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
// import * as THREE from 'three'

// class Home extends HTMLElement {
// 	constructor() {
// 		super();

// 		this.innerHTML = `
// 			<canvas id="background-canvas"></canvas>
// 		`;

// 		this.scene = new THREE.Scene();
// 		this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
// 		this.renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('background-canvas'), alpha: true });

// 		this.renderer.setSize(window.innerWidth, window.innerHeight);
// 		document.body.appendChild(this.renderer.domElement);


// 		this.loader = new GLTFLoader();
// 		this.loader.load('/src/js/utils/scene.gltf', (gltf) => {
// 			this.model = gltf.scene;
// 			this.scene.add(this.model);

// 			// Position and scale the model as needed
// 			this.model.position.set(0, 0, 0);
// 			this.model.scale.set(1, 1, 1);

// 			// Animation handling if any
// 			this.animations = gltf.animations;
// 			if (this.animations && this.animations.length) {
// 				this.mixer = new THREE.AnimationMixer(this.model);
// 				this.animations.forEach((clip) => {
// 					this.mixer.clipAction(clip).play();
// 				});

// 				// Animation loop
// 				this.animate = () => {
// 					requestAnimationFrame(this.animate);
// 					this.mixer.update(0.01);
// 					this.model.rotation.y += 0.01; // Rotate the model for demonstration
// 					this.renderer.render(this.scene, this.camera);
// 				};
// 				this.animate();
// 			} else {
// 				// Simple render loop if no animations
// 				this.animate = () => {
// 					requestAnimationFrame(this.animate);
// 					this.model.rotation.y += 0.01; // Rotate the model for demonstration
// 					this.renderer.render(this.scene, this.camera);
// 				};
// 				this.animate();
// 			}
// 		});


// 		// Handle window resize
// 		window.addEventListener('resize', () => {
// 			this.renderer.setSize(window.innerWidth, window.innerHeight);
// 			this.camera.aspect = window.innerWidth / window.innerHeight;
// 			this.camera.updateProjectionMatrix();
// 		});

// 	}
// }

// customElements.define("home-screen", Home);



// // <video controls width=640 >
// // 				<source src="/static/assets/mushoku-s01-e21.webm" />
// // 				<track
// // 					label="French"
// // 					kind="subtitles"
// // 					srclang="fr"
// // 					src="/static/assets/mushoku-s01-e21.vtt"
// // 					default />
// // 			</video >
// // 	<video controls width=640 >
// // 		<source src="/static/assets/oshi_no_ko-s01-e01.webm" />
// // 			</video >
// // 	<video controls width=640 >
// // 		<source src="/static/assets/nichijou-ed1.mp4" />
// // 			</video >