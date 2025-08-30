#version 330 core

// Input from vertex shader
in vec2 TexCoord;

// Output color
out vec4 FragColor;

// Uniforms
uniform sampler2D textTexture;
uniform vec4 textColor;
uniform vec4 glowColor;
uniform float glowIntensity;
uniform float glowRadius;
uniform vec2 textureSize;

void main() {
    vec2 texelSize = 1.0 / textureSize;
    vec4 color = vec4(0.0);
    
    // Sample the original text
    float originalAlpha = texture(textTexture, TexCoord).r;
    
    // Create glow by sampling surrounding pixels
    float glowAlpha = 0.0;
    int samples = int(glowRadius * 2.0);
    
    for (int x = -samples; x <= samples; x++) {
        for (int y = -samples; y <= samples; y++) {
            vec2 offset = vec2(float(x), float(y)) * texelSize;
            float distance = length(vec2(x, y));
            
            if (distance <= glowRadius) {
                float sample = texture(textTexture, TexCoord + offset).r;
                float falloff = 1.0 - (distance / glowRadius);
                glowAlpha += sample * falloff;
            }
        }
    }
    
    // Normalize glow
    glowAlpha /= float((samples * 2 + 1) * (samples * 2 + 1));
    glowAlpha *= glowIntensity;
    
    // Combine original text with glow
    vec4 glow = glowColor * vec4(1.0, 1.0, 1.0, glowAlpha);
    vec4 text = textColor * vec4(1.0, 1.0, 1.0, originalAlpha);
    
    // Blend glow behind text
    FragColor = mix(glow, text, originalAlpha);
}