#version 330 core

// Vertex attributes
layout (location = 0) in vec2 aPosition;    // Quad vertex position
layout (location = 1) in vec2 aTexCoord;    // Texture coordinates

// Instance attributes
layout (location = 2) in vec3 aInstancePos;    // Particle world position
layout (location = 3) in vec4 aInstanceColor;  // Particle color
layout (location = 4) in float aInstanceSize;  // Particle size
layout (location = 5) in float aInstanceRotation; // Particle rotation

// Uniforms
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

// Outputs to fragment shader
out vec2 texCoord;
out vec4 particleColor;

void main()
{
    // Apply rotation to quad vertex
    float cosR = cos(aInstanceRotation);
    float sinR = sin(aInstanceRotation);
    
    vec2 rotatedPos = vec2(
        aPosition.x * cosR - aPosition.y * sinR,
        aPosition.x * sinR + aPosition.y * cosR
    );
    
    // Scale by particle size
    rotatedPos *= aInstanceSize;
    
    // Transform to world position
    vec3 worldPos = aInstancePos + vec3(rotatedPos, 0.0);
    
    // Transform to clip space
    gl_Position = projectionMatrix * viewMatrix * vec4(worldPos, 1.0);
    
    // Pass through texture coordinates and color
    texCoord = aTexCoord;
    particleColor = aInstanceColor;
}