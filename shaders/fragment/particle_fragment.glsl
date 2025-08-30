#version 330 core

// Inputs from vertex shader
in vec2 texCoord;
in vec4 particleColor;

// Uniforms
uniform sampler2D particleTexture;
uniform bool useTexture = false;

// Output
out vec4 fragColor;

void main()
{
    vec4 color = particleColor;
    
    if (useTexture) {
        // Sample particle texture
        vec4 texColor = texture(particleTexture, texCoord);
        color *= texColor;
    } else {
        // Create a simple circular particle
        vec2 center = vec2(0.5, 0.5);
        float dist = distance(texCoord, center);
        
        // Smooth circular falloff
        float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
        color.a *= alpha;
    }
    
    // Discard fully transparent pixels
    if (color.a < 0.01) {
        discard;
    }
    
    fragColor = color;
}