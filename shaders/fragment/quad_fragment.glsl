#version 330 core

// Input from vertex shader
in vec2 TexCoord;

// Output color
out vec4 FragColor;

// Uniforms
uniform vec4 color;

void main() {
    FragColor = color;
}