#version 330 core

// Input from vertex shader
in vec2 TexCoord;

// Output color
out vec4 FragColor;

// Uniforms
uniform sampler2D textTexture;
uniform vec4 textColor;
uniform vec4 outlineColor;
uniform float outlineWidth;
uniform vec2 textureSize;

void main() {
    vec2 texelSize = 1.0 / textureSize;
    
    // Sample the original text
    float originalAlpha = texture(textTexture, TexCoord).r;
    
    // Create outline by sampling surrounding pixels
    float outlineAlpha = 0.0;
    int samples = int(ceil(outlineWidth));
    
    for (int x = -samples; x <= samples; x++) {
        for (int y = -samples; y <= samples; y++) {
            vec2 offset = vec2(float(x), float(y)) * texelSize;
            float distance = length(vec2(x, y));
            
            if (distance <= outlineWidth && distance > 0.0) {
                float sample = texture(textTexture, TexCoord + offset).r;
                outlineAlpha = max(outlineAlpha, sample);
            }
        }
    }
    
    // Remove original text area from outline
    outlineAlpha = max(0.0, outlineAlpha - originalAlpha);
    
    // Combine original text with outline
    vec4 outline = outlineColor * vec4(1.0, 1.0, 1.0, outlineAlpha);
    vec4 text = textColor * vec4(1.0, 1.0, 1.0, originalAlpha);
    
    // Blend outline behind text
    FragColor = mix(outline, text, originalAlpha);
}