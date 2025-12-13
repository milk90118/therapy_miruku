/**
 * 🌸 Sakura Petal Generator (Simple Version)
 * 
 * 只負責生成 SVG 花瓣形狀
 * 動畫由 CSS @keyframes sakuraFall 控制
 */

class SakuraPetal {
  constructor(container, config = {}) {
    this.container = container;
    this.config = {
      // 花瓣數量
      count: config.count || 35,
      
      // 花瓣大小
      baseSize: config.baseSize || 16,
      sizeVariation: config.sizeVariation || 0.6,
      
      // 顏色
      colors: config.colors || [
        { base: '#ffb7c5', tip: '#ffc9d4', center: '#fff0f3' },
        { base: '#ffc4cf', tip: '#ffd6dd', center: '#fff5f7' },
        { base: '#ffaabb', tip: '#ffbfcc', center: '#ffe8ed' },
        { base: '#ffd0d9', tip: '#ffe0e6', center: '#fffafb' },
        { base: '#ffccd5', tip: '#ffdde3', center: '#fff8f9' },
      ],
      
      // 動畫時間範圍 (秒)
      durationMin: config.durationMin || 12,
      durationMax: config.durationMax || 20,
      
      // 延遲範圍 (秒)
      delayMax: config.delayMax || 12,
      
      ...config
    };
    
    this.init();
  }
  
  /**
   * 生成 SVG 花瓣 - 真實心形缺口
   */
  createPetalSVG(color, size) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 120');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size * 1.2);
    svg.style.overflow = 'visible';
    
    const gradientId = `petal-${Math.random().toString(36).substr(2, 9)}`;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    // 徑向漸層
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
    
    // 葉脈漸層
    const veinGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    veinGradient.setAttribute('id', `${gradientId}-vein`);
    veinGradient.setAttribute('x1', '0%');
    veinGradient.setAttribute('y1', '100%');
    veinGradient.setAttribute('x2', '0%');
    veinGradient.setAttribute('y2', '0%');
    
    const veinStop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    veinStop1.setAttribute('offset', '0%');
    veinStop1.setAttribute('stop-color', color.base);
    veinStop1.setAttribute('stop-opacity', '0.25');
    
    const veinStop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    veinStop2.setAttribute('offset', '100%');
    veinStop2.setAttribute('stop-color', color.center);
    veinStop2.setAttribute('stop-opacity', '0');
    
    veinGradient.appendChild(veinStop1);
    veinGradient.appendChild(veinStop2);
    defs.appendChild(veinGradient);
    
    svg.appendChild(defs);
    
    // 花瓣主體 - 心形缺口
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
    
    // 中心葉脈
    const veinPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    veinPath.setAttribute('d', 'M 50 108 Q 50 65, 50 22');
    veinPath.setAttribute('stroke', `url(#${gradientId}-vein)`);
    veinPath.setAttribute('stroke-width', '2.5');
    veinPath.setAttribute('fill', 'none');
    veinPath.setAttribute('stroke-linecap', 'round');
    
    // 側邊葉脈
    const vein2 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    vein2.setAttribute('d', 'M 50 75 Q 32 60, 22 50');
    vein2.setAttribute('stroke', color.base);
    vein2.setAttribute('stroke-width', '1.2');
    vein2.setAttribute('stroke-opacity', '0.12');
    vein2.setAttribute('fill', 'none');
    
    const vein3 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    vein3.setAttribute('d', 'M 50 75 Q 68 60, 78 50');
    vein3.setAttribute('stroke', color.base);
    vein3.setAttribute('stroke-width', '1.2');
    vein3.setAttribute('stroke-opacity', '0.12');
    vein3.setAttribute('fill', 'none');
    
    svg.appendChild(petalPath);
    svg.appendChild(veinPath);
    svg.appendChild(vein2);
    svg.appendChild(vein3);
    
    return svg;
  }
  
  /**
   * 生成單片花瓣元素
   */
  createPetal(index) {
    const cfg = this.config;
    
    // 隨機大小
    const sizeMultiplier = 0.5 + Math.random() * cfg.sizeVariation;
    const size = cfg.baseSize * sizeMultiplier;
    
    // 隨機顏色
    const color = cfg.colors[Math.floor(Math.random() * cfg.colors.length)];
    
    // 建立容器
    const petal = document.createElement('div');
    petal.className = 'sakura';
    
    // 隨機位置
    petal.style.left = `${Math.random() * 100}%`;
    
    // 隨機動畫時間和延遲 (使用原始 CSS 動畫)
    const duration = cfg.durationMin + Math.random() * (cfg.durationMax - cfg.durationMin);
    const delay = Math.random() * cfg.delayMax;
    petal.style.animationDuration = `${duration}s`;
    petal.style.animationDelay = `${delay}s`;
    
    // 深度效果 (遠近)
    const depth = Math.random();
    const blur = depth < 0.3 ? 0.5 : 0;
    const shadowOpacity = 0.2 + depth * 0.15;
    
    petal.style.filter = `
      drop-shadow(0 2px ${3 + depth * 3}px rgba(255, 183, 197, ${shadowOpacity}))
      ${blur > 0 ? `blur(${blur}px)` : ''}
    `;
    
    // 加入 SVG 花瓣
    const svg = this.createPetalSVG(color, size);
    petal.appendChild(svg);
    
    return petal;
  }
  
  /**
   * 初始化
   */
  init() {
    // 清空容器
    this.container.innerHTML = '';
    
    // 生成花瓣
    for (let i = 0; i < this.config.count; i++) {
      const petal = this.createPetal(i);
      this.container.appendChild(petal);
    }
  }
  
  /**
   * 重新生成
   */
  regenerate() {
    this.init();
  }
  
  /**
   * 更新設定
   */
  setConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
  }
  
  /**
   * 暫停 (透過 CSS class)
   */
  pause() {
    this.container.classList.add('paused');
  }
  
  /**
   * 恢復
   */
  resume() {
    this.container.classList.remove('paused');
  }
  
  /**
   * 清除
   */
  destroy() {
    this.container.innerHTML = '';
  }
}

window.SakuraPetal = SakuraPetal;