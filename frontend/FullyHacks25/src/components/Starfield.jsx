import "./Starfield.css";
import React, { useRef, useEffect } from 'react';

const Starfield = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let stars = [];
    const numStars = 1000;

    // Initialize the stars according to current canvas dimensions.
    const initializeStars = () => {
      stars = [];
      for (let i = 0; i < numStars; i++) {
        stars.push({
          x: (Math.random() - 0.5) * canvas.width,
          y: (Math.random() - 0.5) * canvas.height,
          z: Math.random() * canvas.width,
        });
      }
    };

    // Resize the canvas and reinitialize stars.
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initializeStars();
    };

    // Set initial canvas size and stars.
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const drawStars = () => {
      ctx.fillStyle = 'black';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = 'white';

      for (let i = 0; i < numStars; i++) {
        const star = stars[i];

        // Move the star toward the viewer.
        star.z -= 0.5;

        // Clamp z so that it never exceeds the canvas width.
        if (star.z > canvas.width) {
          star.z = canvas.width;
        }

        // If star has moved past the viewer, reset it.
        if (star.z <= 0) {
          star.z = canvas.width;
          star.x = (Math.random() - 0.5) * canvas.width;
          star.y = (Math.random() - 0.5) * canvas.height;
        }

        const k = 128.0 / star.z;
        const x = star.x * k + canvas.width / 2;
        const y = star.y * k + canvas.height / 2;
        const sizeCalc = (1 - star.z / canvas.width) * 1.5;
        // Ensure that the size is never negative.
        const size = Math.max(sizeCalc, 0);

        // Skip drawing stars that are off-canvas.
        if (x < 0 || x >= canvas.width || y < 0 || y >= canvas.height) continue;

        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(drawStars);
    };

    drawStars();

    return () => window.removeEventListener('resize', resizeCanvas);
  }, []);

  return <canvas id="stars-canvas" ref={canvasRef} />;
};

export default Starfield;
