#version 330 core

// Input from vertex shader
in vec2 TexCoord;
in vec3 WorldPos;

// Output color
out vec4 FragColor;

// Uniforms
uniform sampler2D textTexture;
uniform vec4 gradientStart;
uniform vec4 gradientEnd;
uniform vec2 gradientDirection; // Normalized direction vector
uniform vec2 gradientCenter;    // For radial gradients
uniform float gradientRadius;   // For radial gradients
uniform int gradientType;       // 0=linear, 1=radial, 2=conic

void main() {
    // Sample the text texture
    float textAlpha = texture(textTexture, TexCoord).r;
    
    if (textAlpha < 0.01) {
        discard;
    }
    
    vec4 gradientColor;
    
    if (gradientType == 0) {
        // Linear gradient
        vec2 pos = WorldPos.xy - gradientCenter;
        float t = dot(pos, gradientDirection) / length(gradientDirection);
        t = clamp(t * 0.5 + 0.5, 0.0, 1.0); // Normalize to [0,1]
        gradientColor = mix(gradientStart, gradientEnd, t);
        
    } else if (gradientType == 1) {
        // Radial gradient
        vec2 pos = WorldPos.xy - gradientCenter;
        float distance = length(pos);
        float t = clamp(distance / gradientRadius, 0.0, 1.0);
        gradientColor = mix(gradientStart, gradientEnd, t);
        
    } else if (gradientType == 2) {
        // Conic gradient
        vec2 pos = WorldPos.xy - gradientCenter;
        float angle = atan(pos.y, pos.x);
        float t = (angle + 3.14159) / (2.0 * 3.14159); // Normalize to [0,1]
        gradientColor = mix(gradientStart, gradientEnd, t);
        
    } else {
        // Fallback to start color
        gradientColor = gradientStart;
    }
    
    // Apply gradient color with text alpha
    FragColor = vec4(gradientColor.rgb, gradientColor.a * textAlpha);
}