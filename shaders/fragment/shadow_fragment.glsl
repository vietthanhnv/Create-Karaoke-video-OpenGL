#version 330 core

// Input from vertex shader
in vec2 TexCoord;

// Output color
out vec4 FragColor;

// Uniforms
uniform sampler2D textTexture;
uniform vec4 textColor;
uniform vec4 shadowColor;
uniform vec2 shadowOffset;
uniform float shadowBlur;
uniform vec2 textureSize;

void main() {
    vec2 texelSize = 1.0 / textureSize;
    
    // Sample the original text
    float originalAlpha = texture(textTexture, TexCoord).r;
    
    // Sample shadow at offset position with blur
    float shadowAlpha = 0.0;
    vec2 shadowCoord = TexCoord - shadowOffset * texelSize;
    
    if (shadowBlur > 0.0) {
        // Apply gaussian blur to shadow
        int blurSamples = int(ceil(shadowBlur));
        float totalWeight = 0.0;
        
        for (int x = -blurSamples; x <= blurSamples; x++) {
            for (int y = -blurSamples; y <= blurSamples; y++) {
                vec2 offset = vec2(float(x), float(y)) * texelSize;
                float distance = length(vec2(x, y));
                
                if (distance <= shadowBlur) {
                    float weight = exp(-distance * distance / (2.0 * shadowBlur * shadowBlur));
                    float sample = texture(textTexture, shadowCoord + offset).r;
                    shadowAlpha += sample * weight;
                    totalWeight += weight;
                }
            }
        }
        
        shadowAlpha /= totalWeight;
    } else {
        shadowAlpha = texture(textTexture, shadowCoord).r;
    }
    
    // Combine original text with shadow
    vec4 shadow = shadowColor * vec4(1.0, 1.0, 1.0, shadowAlpha);
    vec4 text = textColor * vec4(1.0, 1.0, 1.0, originalAlpha);
    
    // Blend shadow behind text
    FragColor = mix(shadow, text, originalAlpha);
}