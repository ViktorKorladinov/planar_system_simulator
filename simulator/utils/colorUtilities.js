export function getColorFromGradientRGB(index, length) {
    const normalizedIndex = 1 - index / (length - 1);
    const red = Math.round(255 * (1 - normalizedIndex));
    const blue = Math.round(255 * normalizedIndex);
    const green = 0;
    const opacity = (1 - normalizedIndex);
    return `rgba(${red}, ${green}, ${blue}, ${opacity})`;
}

// Distinct high-contrast thermal palette: every single integer has its own unique shade
const SHADES = [
    '#ffffff', // 0: unvisited
    '#fef08a', // 1: pale soft yellow
    '#fde047', // 2: light canary yellow
    '#facc15', // 3: vibrant gold-yellow
    '#fbbf24', // 4: warm amber gold
    '#f59e0b', // 5: warm amber
    '#f97316', // 6: bright orange
    '#ea580c', // 7: deep burnt orange
    '#ef4444', // 8: bright red
    '#dc2626', // 9: strong vivid red
    '#b91c1c', // 10: deep dark red
    '#991b1b', // 11: rich crimson
    '#7f1d1d', // 12: dark blood red
    '#701a75', // 13: dark ruby magenta
    '#581c87', // 14: deep plum purple
    '#3b0764', // 15: midnight purple
];

export function getColorFromGradient(index, maxPath) {
    if (!index || index <= 0) return '#ffffff';

    const intIdx = Math.round(index);
    if (intIdx < SHADES.length) {
        return SHADES[intIdx];
    }

    // For values beyond 15, smoothly darken into ultra-deep purple
    const excess = intIdx - (SHADES.length - 1);
    const lightness = Math.max(10, 20 - excess * 2);
    return `hsl(275, 80%, ${lightness}%)`;
}