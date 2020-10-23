#! /bin/env python
import extractor

if __name__ == '__main__':
    app = extractor.create_app()
    if not app is None:
        app.run(host='0.0.0.0', debug=app.config['FLASK_DEBUG'], port=app.config['PORT'])