import fs from "fs";

export function createIcons() {
    const shapes = {
        square: (x, y, size, gap = 4) => {
            // Adjust position to account for gaps
            const adjustedX = x + (gap / 2);
            const adjustedY = y + (gap / 2);
            const adjustedSize = size - gap;

            return `<rect x="${adjustedX}" y="${adjustedY}" width="${adjustedSize}" height="${adjustedSize}" fill="none" stroke="black" rx="5" stroke-width="3"/>`;
        }
    };

    const createGrid = (x, y = x, filled = true, cellSize = 100, gap = 4) => {
        // Add extra space to viewBox to accommodate gaps
        const gridSizeX = (cellSize * x) + gap;
        const gridSizeY = (cellSize * y) + gap;
        let grid = '';

        for (let i = 0; i < x; i++) {
            for (let j = 0; j < y; j++) {
                if (filled || i === 0 || i === x - 1 || j === 0 || j === y - 1) {
                    grid += shapes.square(i * cellSize, j * cellSize, cellSize, gap);
                }
            }
        }

        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${gridSizeX} ${gridSizeY}">
    ${grid}
  </svg>`;
    };

    // Create directory if it doesn't exist
    if (!fs.existsSync('public/layouts')) {
        fs.mkdirSync('public/layouts/', { recursive: true });
    }

    // Generate SVGs with gaps
    fs.writeFileSync('public/layouts/square.svg', createGrid(4, 4,true,100,10));
    fs.writeFileSync('public/layouts/doubleline.svg', createGrid(6, 2, true, 100,10));
    fs.writeFileSync('public/layouts/line.svg', createGrid(8, 1, true, 100,10));
    fs.writeFileSync('public/layouts/ring.svg', createGrid(4, 4, false, 100,10));
}