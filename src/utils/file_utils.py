from config import Config

def allowed_file(filename):
    # Comprueba que el nombre tenga extensión y que esté en la lista blanca
    # rsplit con maxsplit=1 garantiza que solo se toma la extensión final
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS