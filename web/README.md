# Job Checker Web Interface

A modern web dashboard for your Job Checker application, built with FastAPI and React.

## Features

- 📊 **Real-time Dashboard** - View job statistics and recent listings
- 🔍 **Advanced Filtering** - Filter by company, source, scope, and search terms
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🚀 **Fast Performance** - Built with modern web technologies
- 🔄 **Live Updates** - Manual refresh button to get latest jobs
- 📈 **Analytics** - Track job trends and company activity

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the web server:**
   ```bash
   cd web
   python main.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:8000`

### Vercel Deployment

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Set environment variables** in Vercel dashboard:
   - `PYTHONPATH`: `.`

## API Endpoints

- `GET /api/jobs` - Get paginated job listings with filters
- `GET /api/jobs/today` - Get today's job listings
- `GET /api/stats` - Get job statistics
- `POST /api/refresh` - Manually refresh jobs
- `GET /api/health` - Health check

## GitHub Integration

The repository includes GitHub Actions for automatic deployment:

1. **Set up Vercel secrets** in your GitHub repository:
   - `VERCEL_TOKEN` - Your Vercel API token
   - `VERCEL_ORG_ID` - Your Vercel organization ID
   - `VERCEL_PROJECT_ID` - Your Vercel project ID

2. **Push to main branch** - Automatic deployment will trigger

## Customization

### Adding New Job Sources

1. Create a new source file in `job_checker/sources/`
2. Update the filtering logic in `job_checker/filtering.py`
3. The web interface will automatically pick up new sources

### Styling

The interface uses Tailwind CSS for styling. Modify `web/static/app.js` to customize the appearance.

### Database Schema

The web interface reads from the existing `job_checker.db` SQLite database. Ensure the database is accessible from your deployment environment.

## Troubleshooting

### Common Issues

1. **Database not found**: Ensure `job_checker.db` is in the project root
2. **Import errors**: Check that `PYTHONPATH` includes the project root
3. **CORS issues**: The API allows all origins by default (restrict in production)

### Local vs Production

- **Local**: Uses SQLite database file
- **Production**: Consider using a cloud database (PostgreSQL, etc.)

## Security Notes

- CORS is currently set to allow all origins
- No authentication is implemented
- Consider adding rate limiting for production use
- Restrict database access in production environments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

Same as the main Job Checker project.
