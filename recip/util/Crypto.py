from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecpy.formatters import decode_sig, encode_sig
from ecpy.keys import ECPublicKey, ECPrivateKey
from ecpy.ecschnorr import ECSchnorr
from ecpy.curves import Curve, Point
from recip.util import Config, DataType
from hashlib import sha256, new
from binascii import unhexlify

def generateHashFromPublic(public):
    verifyKey = VerifyingKey.from_string(public, curve=SECP256k1, hashfunc=sha256)
    return verifyKeyToAddress(verifyKey)

def proofOfWorkHash(data):
    hashAlgorithms = Config.getValues('POW_HASHING_ALGORITHMS')
    for hashAlgorithm in hashAlgorithms: 
        data = generateHash(data, hashAlgorithm)
    return data

def generateHash(data, hashAlgorithm=Config.getValue('DEFAULT_HASHING_ALGORITHM')):
    return _hash(_hash(data, hashAlgorithm), hashAlgorithm)

def _hash(data, hashAlgorithm):
    hashFunction = new(hashAlgorithm, data)
    data = hashFunction.hexdigest()
    return DataType.fromHex(data)
    
def generateKeys():
    signingKey = SigningKey.generate(curve=SECP256k1, hashfunc=sha256)
    verifyKey = signingKey.get_verifying_key()
    return verifyKeyToAddress(verifyKey), keyToBytes(verifyKey), keyToBytes(signingKey)

def verifyKeyToAddress(verifyKey):
    verifyKeyBytes = keyToBytes(verifyKey)
    return generateAddress(verifyKeyBytes)

def generateAddress(data):
    hexdigest = generateHash(data)
    return hexdigest[12:]

def sign(private, message):
    if Config.getBoolValue('SCHNORR_ENABLED'):
        curve = Curve.get_curve('secp256k1')
        signer = ECSchnorr(sha256, "LIBSECP", "ITUPLE")
        private = DataType.bytesToInt(private)
        sig = signer.sign(DataType.serialize(message), ECPrivateKey(private, curve))
        return encode_sig(sig[0], sig[1], 'RAW', 32)
    else:
        signingKey = SigningKey.from_string(unhexlify(private), curve=SECP256k1, hashfunc=sha256)
        return signingKey.sign(DataType.serialize(message)).hex()
    
def verify(public, signature, message):
    verifyKey = VerifyingKey.from_string(public, curve=SECP256k1, hashfunc=sha256)
    if Config.getBoolValue('SCHNORR_ENABLED'):
        curve = Curve.get_curve('secp256k1')
        verifier = ECSchnorr(sha256, "LIBSECP", "ITUPLE")
        x = verifyKey.pubkey.point.x()
        y = verifyKey.pubkey.point.y()
        signature = decode_sig(signature, 'RAW')
        return verifier.verify(DataType.serialize(message), signature, ECPublicKey(Point(x, y, curve)))
    else:
        return verifyKey.verify(unhexlify(signature), DataType.serialize(message))

def keyToBytes(key):
    return key.to_string()
