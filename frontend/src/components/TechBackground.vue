<script>
export default {
  name: 'TechBackground',
  mounted() {
    this.initParticles();
    window.addEventListener('resize', this.resizeCanvas);
  },
  beforeUnmount() {
    cancelAnimationFrame(this.animationFrame);
    window.removeEventListener('resize', this.resizeCanvas);
  },
  methods: {
    initParticles() {
      const canvas = document.getElementById('tech-bg');
      const ctx = canvas.getContext('2d');
      this.canvas = canvas;
      this.ctx = ctx;

      this.resizeCanvas();
      this.particles = [];
      this.createParticles();
      this.animate();
    },
    resizeCanvas() {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
      this.createParticles();
    },
    createParticles() {
      this.particles = [];
      const count = Math.floor((this.canvas.width * this.canvas.height) / 15000);
      for (let i = 0; i < count; i++) {
        this.particles.push({
          x: Math.random() * this.canvas.width,
          y: Math.random() * this.canvas.height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          size: Math.random() * 2 + 1
        });
      }
    },
    animate() {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      // 绘制网格背景（静态）
      ctx.strokeStyle = 'rgba(0, 212, 255, 0.05)';
      ctx.lineWidth = 1;
      for (let x = 0; x < this.canvas.width; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, this.canvas.height); ctx.stroke();
      }
      for (let y = 0; y < this.canvas.height; y += 40) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(this.canvas.width, y); ctx.stroke();
      }

      // 更新并绘制粒子
      for (let i = 0; i < this.particles.length; i++) {
        const p = this.particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;

        ctx.fillStyle = 'rgba(0, 212, 255, 0.6)';
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();

        // 连线
        for (let j = i + 1; j < this.particles.length; j++) {
          const p2 = this.particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 120) {
            ctx.strokeStyle = `rgba(0, 212, 255, ${0.3 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      this.animationFrame = requestAnimationFrame(this.animate);
    }
  }
}
</script>

<template>
  <canvas id="tech-bg"></canvas>
</template>

<style scoped>
#tech-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  background: #0a1929;
}
</style>
