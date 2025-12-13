/**
 * 🌸 Realistic Sakura Petal Animation System
 * Japanese Magazine Style - Gentle Floating Version
 * 
 * Features:
 * - Authentic heart-notched petal shape (SVG)
 * - Gentle floating physics with air resistance
 * - Updraft simulation (偶爾往上飄)
 * - Multi-layer wind currents
 * - Slow, graceful tumbling
 */

class SakuraPetal {
  constructor(container, config = {}) {
    this.container = container;
    this.config = {
      // Petal appearance
      baseSize: config.baseSize || 18,
      sizeVariation: config.sizeVariation || 0.6,
      
      // Colors - authentic sakura palette
      colors: config.colors || [
        { base: '#ffb7c5', tip: '#ffc9d4', center: '#fff0f3' },
        { base: '#ffc4cf', tip: '#ffd6dd', center: '#fff5f7' },
        { base: '#ffaabb', tip: '#ffbfcc', center: '#ffe8ed' },
        { base: '#ffd0d9', tip: '#ffe0e6', center: '#fffafb' },
        { base: '#ffccd5', tip: '#ffdde3', center: '#fff8f9' },
      ],
      
      // 🌸 Gentle Physics - 緩緩飄落
      fallSpeed: config.fallSpeed || { min: 15, max: 35 },
      swayAmplitude: config.swayAmplitude || { min: 40, max: 100 },
      swayFrequency: config.swayFrequency || { min: 0.3, max: 0.7 },
      
      // 🌸 Slow rotation - 優雅翻轉
      rotationSpeed: config.rotationSpeed || { min: 8, max: 25 },
      tumbleSpeed: config.tumbleSpeed || { min: 10, max: 30 },
      
      // 🌸 Air dynamics - 空氣動力學
      airResistance: config.airResistance || 0.985,
      updraftStrength: config.updraftStrength || 0.4,
      updraftFrequency: config.updraftFrequency || 0.15,
      
      // Wind system
      windEnabled: config.windEnabled !== false,
      windStrength: config.windStrength || 0.2,
      windGustInterval: config.windGustInterval || 6000,
      
      // Spawn settings
      spawnRate: config.spawnRate || 400,
      maxPetals: config.maxPetals || 30,
      
      ...config
    };
    
    this.petals = [];
    this.wind = { x: 0, y: 0, gust: 0 };
    this.animationId = null;
    this.lastTime = 0;
    this.spawnTimer = 0;
    this.isPaused = false;
    this.globalTime = 0;
    
    this.init();
  }
  
  /**
   * Generate SVG petal with authentic heart-notched shape
   */
  createPetalSVG(color, size) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 120');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size * 1.2);
    svg.style.overflow = 'visible';
    
    const gradientId = `petal-gradient-${Math.random().toString(36).substr(2, 9)}`;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    // Radial gradient for petal depth
    const radialGradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
    radialGradient.setAttribute('id', gradientId);
    radialGradient.setAttribute('cx', '30%');
    radialGradient.setAttribute('cy', '40%');
    radialGradient.setAttribute('r', '70%');
    
    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('stop-color', color.center);
    
    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '50%');
    stop2.setAttribute('stop-color', color.tip);
    
    const stop3 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop3.setAttribute('offset', '100%');
    stop3.setAttribute('stop-color', color.base);
    
    radialGradient.appendChild(stop1);
    radialGradient.appendChild(stop2);
    radialGradient.appendChild(stop3);
    defs.appendChild(radialGradient);
    
    // Vein gradient
    const veinGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    veinGradient.setAttribute('id', `${gradientId}-vein`);
    veinGradient.setAttribute('x1', '0%');
    veinGradient.setAttribute('y1', '100%');
    veinGradient.setAttribute('x2', '0%');
    veinGradient.setAttribute('y2', '0%');
    
    const veinStop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    veinStop1.setAttribute('offset', '0%');
    veinStop1.setAttribute('stop-color', color.base);
    veinStop1.setAttribute('stop-opacity', '0.3');
    
    const veinStop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    veinStop2.setAttribute('offset', '100%');
    veinStop2.setAttribute('stop-color', color.center);
    veinStop2.setAttribute('stop-opacity', '0');
    
    veinGradient.appendChild(veinStop1);
    veinGradient.appendChild(veinStop2);
    defs.appendChild(veinGradient);
    
    svg.appendChild(defs);
    
    // Main petal path - authentic sakura shape with heart notch
    const petalPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    petalPath.setAttribute('d', `
      M 50 115
      C 25 115, 5 90, 5 60
      C 5 30, 25 5, 42 5
      C 46 5, 48 8, 50 15
      C 52 8, 54 5, 58 5
      C 75 5, 95 30, 95 60
      C 95 90, 75 115, 50 115
      Z
    `);
    petalPath.setAttribute('fill', `url(#${gradientId})`);
    petalPath.setAttribute('stroke', 'none');
    
    // Center vein
    const veinPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    veinPath.setAttribute('d', 'M 50 110 Q 50 70, 50 25');
    veinPath.setAttribute('stroke', `url(#${gradientId}-vein)`);
    veinPath.setAttribute('stroke-width', '2');
    veinPath.setAttribute('fill', 'none');
    veinPath.setAttribute('stroke-linecap', 'round');
    
    // Secondary veins
    const vein2 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    vein2.setAttribute('d', 'M 50 80 Q 35 65, 25 55');
    vein2.setAttribute('stroke', color.base);
    vein2.setAttribute('stroke-width', '1');
    vein2.setAttribute('stroke-opacity', '0.15');
    vein2.setAttribute('fill', 'none');
    
    const vein3 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    vein3.setAttribute('d', 'M 50 80 Q 65 65, 75 55');
    vein3.setAttribute('stroke', color.base);
    vein3.setAttribute('stroke-width', '1');
    vein3.setAttribute('stroke-opacity', '0.15');
    vein3.setAttribute('fill', 'none');
    
    svg.appendChild(petalPath);
    svg.appendChild(veinPath);
    svg.appendChild(vein2);
    svg.appendChild(vein3);
    
    return svg;
  }
  
  /**
   * Create a petal DOM element with physics properties
   */
  createPetal() {
    const cfg = this.config;
    
    const depthLayer = Math.random();
    const sizeMultiplier = 0.4 + (cfg.sizeVariation * depthLayer) + (Math.random() * 0.4);
    const size = cfg.baseSize * sizeMultiplier;
    
    const color = cfg.colors[Math.floor(Math.random() * cfg.colors.length)];
    
    const element = document.createElement('div');
    element.className = 'sakura-petal';
    element.style.cssText = `
      position: absolute;
      pointer-events: none;
      transform-style: preserve-3d;
      will-change: transform, opacity;
      filter: drop-shadow(0 2px ${4 * depthLayer}px rgba(255, 183, 197, ${0.2 + 0.2 * depthLayer}));
    `;
    
    const svg = this.createPetalSVG(color, size);
    element.appendChild(svg);
    
    // 🌸 Enhanced physics properties for gentle floating
    const petal = {
      element,
      size,
      depthLayer,
      
      x: Math.random() * (this.container.offsetWidth + 100) - 50,
      y: -size * 2,
      
      vx: (Math.random() - 0.5) * 8,
      vy: this.randomRange(cfg.fallSpeed.min, cfg.fallSpeed.max) * (0.5 + 0.5 * depthLayer),
      
      baseFallSpeed: this.randomRange(cfg.fallSpeed.min, cfg.fallSpeed.max) * (0.5 + 0.5 * depthLayer),
      
      rotateX: Math.random() * 360,
      rotateY: Math.random() * 360,
      rotateZ: Math.random() * 360,
      
      rotateXSpeed: this.randomRange(cfg.tumbleSpeed.min, cfg.tumbleSpeed.max) * (Math.random() > 0.5 ? 1 : -1),
      rotateYSpeed: this.randomRange(cfg.tumbleSpeed.min, cfg.tumbleSpeed.max) * (Math.random() > 0.5 ? 1 : -1),
      rotateZSpeed: this.randomRange(cfg.rotationSpeed.min, cfg.rotationSpeed.max) * (Math.random() > 0.5 ? 1 : -1),
      
      // 🌸 Multi-wave sway
      swayPhase1: Math.random() * Math.PI * 2,
      swayPhase2: Math.random() * Math.PI * 2,
      swayAmplitude: this.randomRange(cfg.swayAmplitude.min, cfg.swayAmplitude.max),
      swayFrequency1: this.randomRange(cfg.swayFrequency.min, cfg.swayFrequency.max),
      swayFrequency2: this.randomRange(cfg.swayFrequency.min * 1.5, cfg.swayFrequency.max * 2),
      
      flutterPhase: Math.random() * Math.PI * 2,
      flutterSpeed: 1 + Math.random() * 2,
      
      updraftPhase: Math.random() * Math.PI * 2,
      updraftSensitivity: 0.5 + Math.random() * 0.5,
      
      airLayerOffset: Math.random() * 1000,
      
      opacity: 0,
      maxOpacity: 0.75 + 0.25 * depthLayer,
      
      age: 0,
      fadeInDuration: 1.0,
      alive: true
    };
    
    this.container.appendChild(element);
    return petal;
  }
  
  /**
   * Update wind system
   */
  updateWind(deltaTime) {
    if (!this.config.windEnabled) return;
    
    const targetWindX = Math.sin(this.globalTime / 12000) * this.config.windStrength * 20;
    this.wind.x += (targetWindX - this.wind.x) * deltaTime * 0.3;
    
    if (Math.random() < deltaTime / (this.config.windGustInterval / 1000)) {
      this.wind.gust = (Math.random() - 0.3) * 25 * this.config.windStrength;
    }
    this.wind.gust *= 0.98;
  }
  
  /**
   * Calculate air current at specific height
   */
  getAirCurrentAtHeight(y, time, offset) {
    const containerHeight = this.container.offsetHeight;
    const normalizedY = y / containerHeight;
    
    const layer1 = Math.sin((time + offset) / 3000 + normalizedY * 2) * 8;
    const layer2 = Math.sin((time + offset) / 5000 - normalizedY * 3) * 5;
    const layer3 = Math.cos((time + offset) / 7000 + normalizedY) * 3;
    
    return layer1 + layer2 + layer3;
  }
  
  /**
   * Update single petal physics
   */
  updatePetal(petal, deltaTime) {
    const cfg = this.config;
    petal.age += deltaTime;
    
    // Gentle fade in
    if (petal.age < petal.fadeInDuration) {
      petal.opacity = (petal.age / petal.fadeInDuration) * petal.maxOpacity;
    }
    
    // 🌸 Multi-wave sway
    const sway1 = Math.sin(petal.swayPhase1 + petal.age * petal.swayFrequency1 * Math.PI * 2) 
                  * petal.swayAmplitude * 0.7;
    const sway2 = Math.sin(petal.swayPhase2 + petal.age * petal.swayFrequency2 * Math.PI * 2) 
                  * petal.swayAmplitude * 0.3;
    const totalSway = (sway1 + sway2) * deltaTime;
    
    // 🌸 Gentle flutter
    const flutter = Math.sin(petal.flutterPhase + petal.age * petal.flutterSpeed * Math.PI * 2) 
                    * 2 * deltaTime;
    
    // 🌸 Air current effect
    const airCurrent = this.getAirCurrentAtHeight(petal.y, this.globalTime, petal.airLayerOffset);
    
    // 🌸 Updraft
    let updraft = 0;
    if (Math.random() < cfg.updraftFrequency * deltaTime) {
      updraft = -cfg.updraftStrength * petal.baseFallSpeed * petal.updraftSensitivity 
                * (0.5 + Math.random() * 0.5);
    }
    const gentleUplift = Math.sin(petal.updraftPhase + petal.age * 0.5) * 3 * petal.updraftSensitivity;
    
    // Apply forces
    petal.vx += (this.wind.x + this.wind.gust + airCurrent) * deltaTime * (0.3 + 0.4 * petal.depthLayer);
    petal.vx *= cfg.airResistance;
    
    petal.vy += updraft * deltaTime;
    petal.vy += gentleUplift * deltaTime;
    
    if (petal.vy < petal.baseFallSpeed * 0.3) {
      petal.vy += (petal.baseFallSpeed * 0.5 - petal.vy) * deltaTime * 0.5;
    }
    if (petal.vy > petal.baseFallSpeed * 1.5) {
      petal.vy = petal.baseFallSpeed * 1.5;
    }
    
    petal.vy *= cfg.airResistance;
    
    petal.x += petal.vx * deltaTime + totalSway + flutter;
    petal.y += petal.vy * deltaTime;
    
    // 🌸 Gentle 3D rotation
    const rotationVariation = 1 + Math.sin(petal.age * 0.8) * 0.2;
    petal.rotateX += petal.rotateXSpeed * deltaTime * rotationVariation;
    petal.rotateY += petal.rotateYSpeed * deltaTime * rotationVariation;
    petal.rotateZ += petal.rotateZSpeed * deltaTime * rotationVariation * 0.7;
    
    // Check bounds
    const containerHeight = this.container.offsetHeight;
    const containerWidth = this.container.offsetWidth;
    
    if (petal.y > containerHeight + petal.size || 
        petal.x < -petal.size * 3 || 
        petal.x > containerWidth + petal.size * 3) {
      petal.alive = false;
      return;
    }
    
    // Gentle fade out
    const fadeOutStart = containerHeight * 0.75;
    if (petal.y > fadeOutStart) {
      const fadeProgress = (petal.y - fadeOutStart) / (containerHeight - fadeOutStart);
      petal.opacity = petal.maxOpacity * (1 - fadeProgress * fadeProgress);
    }
    
    petal.element.style.transform = `
      translate3d(${petal.x}px, ${petal.y}px, ${petal.depthLayer * 50}px)
      rotateX(${petal.rotateX}deg)
      rotateY(${petal.rotateY}deg)
      rotateZ(${petal.rotateZ}deg)
    `;
    petal.element.style.opacity = petal.opacity;
  }
  
  /**
   * Main animation loop
   */
  animate(currentTime) {
    if (this.isPaused) return;
    
    const deltaTime = Math.min((currentTime - this.lastTime) / 1000, 0.1);
    this.lastTime = currentTime;
    this.globalTime = currentTime;
    
    this.updateWind(deltaTime);
    
    this.spawnTimer += deltaTime * 1000;
    if (this.spawnTimer >= this.config.spawnRate && this.petals.length < this.config.maxPetals) {
      this.petals.push(this.createPetal());
      this.spawnTimer = 0;
    }
    
    for (let i = this.petals.length - 1; i >= 0; i--) {
      const petal = this.petals[i];
      this.updatePetal(petal, deltaTime);
      
      if (!petal.alive) {
        petal.element.remove();
        this.petals.splice(i, 1);
      }
    }
    
    this.animationId = requestAnimationFrame((t) => this.animate(t));
  }
  
  randomRange(min, max) {
    return min + Math.random() * (max - min);
  }
  
  init() {
    this.container.style.perspective = '1000px';
    this.container.style.perspectiveOrigin = '50% 50%';
    this.lastTime = performance.now();
    this.animate(this.lastTime);
  }
  
  pause() {
    this.isPaused = true;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }
  
  resume() {
    if (this.isPaused) {
      this.isPaused = false;
      this.lastTime = performance.now();
      this.animate(this.lastTime);
    }
  }
  
  destroy() {
    this.pause();
    this.petals.forEach(petal => petal.element.remove());
    this.petals = [];
  }
  
  setConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
  }
  
  triggerGust(strength = 1) {
    this.wind.gust = (Math.random() > 0.5 ? 1 : -1) * 30 * strength;
  }
}

window.SakuraPetal = SakuraPetal;