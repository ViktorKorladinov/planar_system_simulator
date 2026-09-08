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
    const normalizedIndex = 1 - index / (maxPath - 1) * 0.5;
    return `hsl(${normalizedIndex * 20}, 100%, ${normalizedIndex * 100}%)`;
}