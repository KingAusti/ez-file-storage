# Cloudflare Tunnel Setup Guide

This guide will help you set up Cloudflare Tunnel to expose your data storage application to the internet securely.

## Prerequisites

- A domain name (you can get one from various providers)
- Cloudflare account (free tier is sufficient)

## Step 1: Set Up Your Domain with Cloudflare

1. **Sign up for Cloudflare**: Go to [cloudflare.com](https://www.cloudflare.com) and create an account

2. **Add your domain**: 
   - Click "Add a Site" in your Cloudflare dashboard
   - Enter your domain name
   - Choose the free plan

3. **Update nameservers**: 
   - Cloudflare will provide you with nameservers
   - Update your domain's nameservers at your domain registrar
   - Wait for DNS propagation (can take up to 24 hours)

## Step 2: Install Cloudflare Tunnel

### macOS
```bash
brew install cloudflared
```

### Linux
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Windows
Download from: https://github.com/cloudflare/cloudflared/releases

## Step 3: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will open a browser window for you to authenticate with Cloudflare.

## Step 4: Create a Tunnel

```bash
cloudflared tunnel create data-storage-app
```

This will create a tunnel and save the credentials file.

## Step 5: Configure DNS

```bash
cloudflared tunnel route dns data-storage-app your-subdomain.yourdomain.com
```

Replace `your-subdomain.yourdomain.com` with your desired subdomain.

## Step 6: Create Configuration File

Create a configuration file at `~/.cloudflared/config.yml`:

```yaml
tunnel: data-storage-app
credentials-file: /Users/your-username/.cloudflared/data-storage-app.json

ingress:
  - hostname: your-subdomain.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

**Important**: Update the `credentials-file` path to match your system and the `hostname` to your subdomain.

## Step 7: Run the Tunnel

```bash
cloudflared tunnel run data-storage-app
```

Your application will now be accessible at `https://your-subdomain.yourdomain.com`

## Step 8: Set Up as a Service (Optional)

To run the tunnel automatically on system startup:

### macOS (using launchd)
```bash
sudo cloudflared service install
```

### Linux (using systemd)
```bash
sudo cloudflared service install
```

## Security Considerations

1. **Update CORS settings**: In your backend `app/main.py`, update the CORS origins to include your domain:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",
           "https://your-subdomain.yourdomain.com"
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Environment variables**: Make sure to use secure environment variables in production:
   ```bash
   SECRET_KEY=your-very-secure-secret-key-here
   ```

3. **Database**: Consider using a production database like PostgreSQL instead of SQLite for better performance and reliability.

## Troubleshooting

### Tunnel not connecting
- Check if your backend is running on port 8000
- Verify the configuration file path and content
- Check Cloudflare dashboard for tunnel status

### DNS not resolving
- Wait for DNS propagation (up to 24 hours)
- Check if nameservers are correctly set
- Verify the DNS record in Cloudflare dashboard

### CORS errors
- Update CORS origins in your backend configuration
- Check browser developer tools for specific error messages

## Monitoring

You can monitor your tunnel status in the Cloudflare dashboard under "Zero Trust" > "Access" > "Tunnels".

## Cost

Cloudflare Tunnel is free for personal use. The free tier includes:
- Unlimited tunnels
- Unlimited bandwidth
- Basic DDoS protection
- SSL/TLS encryption

For more information, visit the [Cloudflare Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/).
