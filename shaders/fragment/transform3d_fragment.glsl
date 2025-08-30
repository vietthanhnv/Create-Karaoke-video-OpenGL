#version 330 core

// Input from vertex shader
in vec2 TexCoord;
in vec3 WorldPos;
in vec3 Normal;

// Output color
out vec4 FragColor;

// Uniforms
uniform sampler2D textTexture;
uniform vec4 textColor;
uniform vec3 lightDirection;
uniform vec4 ambientColor;
uniform vec4 diffuseColor;
uniform float shininess;

void main() {
    // Sample the text texture
    float textAlpha = texture(textTexture, TexCoord).r;
    
    if (textAlpha < 0.01) {
        discard;
    }
    
    // Calculate lighting
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(-lightDirection);
    
    // Ambient lighting
    vec4 ambient = ambientColor;
    
    // Diffuse lighting
    float diff = max(dot(norm, lightDir), 0.0);
    vec4 diffuse = diff * diffuseColor;
    
    // Combine lighting with text color
    vec4 litColor = textColor * (ambient + diffuse);
    
    // Apply text alpha
    FragColor = vec4(litColor.rgb, litColor.a * textAlpha);
}