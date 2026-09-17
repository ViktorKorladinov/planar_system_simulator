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

    // Proportionate to overall steps (maxPath):
    // Bottlenecked tiles typically receive ~20-25% of total simulation steps
    const ceiling = Math.max(6, Math.round((maxPath || 50) * 0.22));
    const rawRatio = Math.min(1, index / ceiling);

    // Non-linear power curve: starts off very slow (subtle pale tint),
    // then warms through gold and orange, hitting deep RED RED at peak
    const t = Math.pow(rawRatio, 1.7);

    const hue = Math.round(54 * (1 - t));
    const lightness = Math.round(92 - 50 * t);
    const saturation = Math.round(70 + 30 * t);

    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}