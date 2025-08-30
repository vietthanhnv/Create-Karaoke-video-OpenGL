#version 330 core

// Vertex attributes
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 texCoord;

// Uniforms
uniform mat4 projection;

// Output to fragment shader
out vec2 TexCoord;

void main() {
    gl_Position = projection * vec4(position, 1.0);
    TexCoord = texCoord;
}