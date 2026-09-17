export function getColorFromGradientRGB(index, length) {
    // if (index==0) return `transparent`
    const normalizedIndex = 1 - index / (length - 1);
    const red = Math.round(255 * (1 - normalizedIndex));
    const blue = Math.round(255 * normalizedIndex);
    const green = 0
    const opacity = (1-normalizedIndex)
    return `rgba(${red}, ${green}, ${blue}, ${opacity})`;
}

export function getColorFromGradient(index, maxPath) {
    if (!index || index <= 0) return '#ffffff';

    // Ramped-up traffic saturation: tiles reach deep red around 10-15 visits
    const effectiveMax = Math.max(6, Math.min(20, Math.floor((maxPath || 60) * 0.15)));
    const ratio = Math.min(1, Math.max(0, index / effectiveMax));

    // Thermal heatmap scale:
    // Low: bright warm yellow (hsl(50, 100%, 78%))
    // Mid: vivid orange (hsl(28, 100%, 58%))
    // High: deep crimson red (hsl(0, 100%, 42%))
    const hue = Math.round(50 * (1 - ratio));
    const lightness = Math.round(78 - 36 * Math.pow(ratio, 0.8));

    return `hsl(${hue}, 100%, ${lightness}%)`;
}