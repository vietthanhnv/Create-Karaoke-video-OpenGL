#version 330 core

// Vertex attributes
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 texCoord;

// Uniforms
uniform mat4 projection;
uniform mat4 model;

// Output to fragment shader
out vec2 TexCoord;
out vec3 WorldPos;

void main() {
    vec4 worldPos = model * vec4(position, 1.0);
    WorldPos = worldPos.xyz;
    gl_Position = projection * worldPos;
    TexCoord = texCoord;
}