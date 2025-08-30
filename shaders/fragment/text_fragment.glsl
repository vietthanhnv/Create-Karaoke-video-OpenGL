#version 330 core

// Input from vertex shader
in vec2 TexCoord;

// Output color
out vec4 FragColor;

// Uniforms
uniform sampler2D textTexture;
uniform vec4 textColor;

void main() {
    // Sample the text texture (alpha channel contains glyph data)
    vec4 sampled = vec4(1.0, 1.0, 1.0, texture(textTexture, TexCoord).r);
    
    // Apply text color with alpha from texture
    FragColor = textColor * sampled;
}