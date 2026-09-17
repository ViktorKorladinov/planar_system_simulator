export function getColorFromGradientRGB(index, length) {
    const normalizedIndex = 1 - index / (length - 1);
    const red = Math.round(255 * (1 - normalizedIndex));
    const blue = Math.round(255 * normalizedIndex);
    const green = 0;
    const opacity = (1 - normalizedIndex);
    return `rgba(${red}, ${green}, ${blue}, ${opacity})`;
}

// Smooth thermal heatmap palette: gradual progression across 0–50+ without premature darkening
const SHADES = [
    '#ffffff', // 0: unvisited
    '#fef08a', // 1: pale soft yellow
    '#feeb74', // 2
    '#fde55d', // 3
    '#fde047', // 4: canary yellow
    '#fbd038', // 5
    '#f9bf29', // 6: warm gold
    '#f7af1a', // 7
    '#f59e0b', // 8: amber
    '#f6950d', // 9
    '#f78d0f', // 10: golden orange
    '#f78412', // 11
    '#f87c14', // 12
    '#f97316', // 13: bright orange
    '#f76a1f', // 14
    '#f56028', // 15
    '#f35732', // 16: vermilion
    '#f14d3b', // 17
    '#ef4444', // 18: bright red
    '#e63d3d', // 19
    '#dd3737', // 20: crimson
    '#d43030', // 21
    '#cb2929', // 22
    '#c22323', // 23
    '#b91c1c', // 24: deep red
    '#b11c2f', // 25: ruby crimson (clearly visible and red)
    '#a81b42', // 26: deep ruby
    '#a01b56', // 27
    '#971a69', // 28: berry magenta
    '#8f1a7c', // 29
    '#86198f', // 30: rich fuchsia/purple
    '#7e1a8e', // 31
    '#771a8c', // 32
    '#6f1b8b', // 33
    '#671b8a', // 34: royal violet
    '#601c88', // 35
    '#581c87', // 36: deep royal purple
    '#531981', // 37
    '#4e157b', // 38
    '#4a1276', // 39
    '#450e70', // 40: midnight violet (clearly tinted purple)
    '#400b6a', // 41
    '#3b0764', // 42: dark midnight purple
    '#370a61', // 43
    '#340c5e', // 44
    '#300f5b', // 45: deep plum
    '#2d1158', // 46
    '#291454', // 47
    '#251651', // 48
    '#22194e', // 49
    '#1e1b4b', // 50: dark navy indigo
];

export function getColorFromGradient(index, maxPath) {
    if (!index || index <= 0) return '#ffffff';

    const intIdx = Math.round(index);
    if (intIdx < SHADES.length) {
        return SHADES[intIdx];
    }

    // For values beyond 50, smoothly preserve dark navy indigo
    return SHADES[SHADES.length - 1];
}

export function getTextColorForIndex(index) {
    if (!index || index <= 0) return '#1e293b';
    const intIdx = Math.round(index);
    return intIdx >= 18 ? '#ffffff' : '#1e293b';
}