#version 330 core

// Input from vertex shader
in vec2 TexCoord;
in vec3 WorldPos;

// Output color
out vec4 FragColor;

// Uniforms
uniform sampler2D textTexture;
uniform vec4 baseColor;
uniform float time;
uniform int animationType; // 0=rainbow, 1=pulse, 2=strobe
uniform float animationSpeed;
uniform float bpm; // For BPM synchronization

// HSV to RGB conversion
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    // Sample the text texture
    float textAlpha = texture(textTexture, TexCoord).r;
    
    if (textAlpha < 0.01) {
        discard;
    }
    
    vec4 animatedColor = baseColor;
    
    if (animationType == 0) {
        // Rainbow cycling
        float hue = fract(time * animationSpeed + WorldPos.x * 0.01);
        vec3 rainbowColor = hsv2rgb(vec3(hue, 1.0, 1.0));
        animatedColor = vec4(rainbowColor, baseColor.a);
        
    } else if (animationType == 1) {
        // Pulse animation (can be BPM synchronized)
        float pulseTime = time * animationSpeed;
        if (bpm > 0.0) {
            pulseTime = time * (bpm / 60.0);
        }
        float pulse = sin(pulseTime) * 0.5 + 0.5;
        animatedColor = baseColor * (0.5 + pulse * 0.5);
        
    } else if (animationType == 2) {
        // Strobe effect
        float strobeTime = time * animationSpeed;
        float strobe = step(0.5, fract(strobeTime));
        animatedColor = baseColor * strobe;
    }
    
    // Apply animated color with text alpha
    FragColor = vec4(animatedColor.rgb, animatedColor.a * textAlpha);
}