#version 330 core

// Vertex attributes
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 texCoord;

// Uniforms
uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;
uniform mat4 transform3D;
uniform float extrusionDepth;

// Output to fragment shader
out vec2 TexCoord;
out vec3 WorldPos;
out vec3 Normal;

void main() {
    // Apply 3D transformation
    vec4 transformedPos = transform3D * vec4(position, 1.0);
    
    // Add extrusion depth if needed
    if (extrusionDepth > 0.0) {
        transformedPos.z += extrusionDepth;
    }
    
    // Calculate world position
    vec4 worldPos = model * transformedPos;
    WorldPos = worldPos.xyz;
    
    // Calculate normal (simplified for text quads)
    Normal = normalize((model * transform3D * vec4(0.0, 0.0, 1.0, 0.0)).xyz);
    
    // Final position
    gl_Position = projection * view * worldPos;
    TexCoord = texCoord;
}