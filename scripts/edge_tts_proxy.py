#!/usr/bin/env python3
"""edge-tts'i ortamın CA paketiyle çalıştırır (proxy sertifikası). Argümanlar edge-tts ile aynı."""
import os, ssl, sys
import edge_tts.communicate as c
ca = os.environ.get("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt")
c._SSL_CTX = ssl.create_default_context(cafile=ca)
from edge_tts.util import main
sys.exit(main())
