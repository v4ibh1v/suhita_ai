# import asyncio
# import logging
# import os
# import re
# from typing import Optional, Annotated

# from dotenv import load_dotenv
# from livekit.agents import (
#     AutoSubscribe,
#     JobContext,
#     llm,
#     multimodal,
#     cli,
#     tokenize,
#     tts,
# )
# from livekit.agents.llm import ChatContext, ChatMessage, FunctionContext
# from livekit.plugins import google
# from livekit.rtc import Track, TrackKind, VideoStream, ConnectionState
# from llama_index.core import (
#     SimpleDirectoryReader,
#     StorageContext,
#     VectorStoreIndex,
#     load_index_from_storage,
# )
# import requests

# logger = logging.getLogger("vision-assistant")
# logger.setLevel(logging.DEBUG)
# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
# logger.addHandler(handler)

# SPEAKING_FRAME_RATE = 1.0
# NOT_SPEAKING_FRAME_RATE = 0.5
# JPEG_QUALITY = 80

# # Load environment variables from .env.local
# load_dotenv(dotenv_path=".env.local")

# # Initialize RAG components
# PERSIST_DIR = "./dental-knowledge-storage"
# if not os.path.exists(PERSIST_DIR):
#     documents = SimpleDirectoryReader("medical_data").load_data()
#     index = VectorStoreIndex.from_documents(documents)
#     index.storage_context.persist(persist_dir=PERSIST_DIR)
# else:
#     storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
#     index = load_index_from_storage(storage_context)

# _SYSTEM_PROMPT = """
# You are a medical assistant named "Suhita". You are designed to provide concise, accurate, and friendly answers only to medical-related queries.
# If the user asks questions outside the realm of medicine, you should reply with a message such as: "I'm sorry, I can only answer medical related questions."
# Your user interacts with you via a smartphone app and may speak using their microphone or share video from their camera or screen.
# When a video is shared, you may use the visual context to better understand the user's situation, but always remain within medical expertise.
# Always provide your responses in a way that is clear and supportive, avoiding medical jargon when possible.
# Remember: you are a medical assistant. Do not provide advice outside the scope of medical information.
# """

# class DentalAssistantFunction(FunctionContext):
#     @llm.ai_callable(
#         description="Called when user asked a Query that can be fetched using dental knowledge base for specific information"
#     )
#     async def query_dental_info(
#         self,
#         query: Annotated[
#             str,
#             llm.TypeInfo(
#                 description="The user asked query to search in the dental knowledge base"
#             )
#         ],
#     ):
#         print(f"Answering from knowledgebase {query}")
#         query_engine = index.as_query_engine(use_async=True)
#         res = await query_engine.aquery(query)
#         print("Query result:", res)
#         return str(res)

#     @llm.ai_callable(
#         description="Called when asked to evaluate dental issues using vision capabilities"
#     )
#     async def analyze_dental_image(
#         self,
#         user_msg: Annotated[
#             str,
#             llm.TypeInfo(
#                 description="The user message that triggered this function"
#             )
#         ],
#     ):
#         print(f"Analyzing dental image: {user_msg}")
#         # Add logic to analyze the dental image using the video frames
#         return "Image analysis result"

#     @llm.ai_callable(
#         description="Called when a user wants to book an appointment"
#     )
#     async def book_appointment(
#         self,
#         email: Annotated[str, llm.TypeInfo(description="Email address")],
#         name: Annotated[str, llm.TypeInfo(description="Patient name")],
#     ):
#         if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
#             return "The email address seems incorrect. Please provide a valid one."

#         try:
#             webhook_url = os.getenv('WEBHOOK_URL')
#             headers = {'Content-Type': 'application/json'}
#             data = {'email': email, 'name': name}
#             response = requests.post(webhook_url, json=data, headers=headers)
#             response.raise_for_status()
#             return f"Dental appointment booking link sent to {email}. Please check your email."
#         except requests.RequestException as e:
#             print(f"Error booking appointment: {e}")
#             return "There was an error booking your dental appointment. Please try again later."

#     @llm.ai_callable(
#         description="Assess the urgency of a dental issue"
#     )
#     async def assess_dental_urgency(
#         self,
#         symptoms: Annotated[str, llm.TypeInfo(description="Dental symptoms")],
#     ):
#         urgent_keywords = ["severe pain", "swelling", "bleeding", "trauma", "knocked out", "broken"]
#         if any(keyword in symptoms.lower() for keyword in urgent_keywords):
#             return "call_human_agent"
#         else:
#             return "Your dental issue doesn't appear to be immediately urgent, but it's still important to schedule an appointment soon for a proper evaluation."

# class VisionAssistant:
#     def __init__(self):
#         self.agent: Optional[multimodal.MultimodalAgent] = None
#         self.model: Optional[google.beta.realtime.RealtimeModel] = None
#         self._is_user_speaking: bool = False

#     async def start(self, ctx: JobContext):
#         await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
#         participant = await ctx.wait_for_participant()
#         logger.info(f"Connected. Using participant: {participant.identity}")

#         chat_ctx = llm.ChatContext(
#             messages=[
#                 ChatMessage(
#                     role="system",
#                     content=(
#                         "Your name is Suhita, a dental assistant for Knolabs Dental Agency. You are soft, caring with a bit of humour when responding. "
#                         "You have access to a comprehensive dental knowledge base that includes various services, price info, and policy details, which you can reference or query to provide accurate information about dental procedures, conditions, and care. "
#                         "You offer appointment booking for dental care services, including urgent attention, routine check-ups, and long-term treatments. An onsite appointment is required in most cases. "
#                         "You can also analyze dental images to provide preliminary assessments, but always emphasize the need for a professional in-person examination. "
#                         "Provide friendly, professional assistance and emphasize the importance of regular dental care. "
#                         "Ask questions one by one and ensure you get the patient's name and email address in sequence if not already provided, encouraging the user to confirm their email to avoid any mistakes. "
#                         "If the care needed is not urgent, you may ask for an image or request the user to show the dental area so you can use your vision capabilities for analysis. "
#                         "Always keep your conversation engaging with multiple interactions, even when the information shared is lengthy, and try to offer an in-person appointment. "
#                         "Additionally, you understand English, Hindi, and Marathi. If a user speaks or types in Hindi or Marathi, please process the input accordingly and respond in that language."
#                     ),
#                 )
#             ]
#         )

#         self.model = google.beta.realtime.RealtimeModel(
#             voice="Puck",
#             temperature=0.8,
#             instructions=_SYSTEM_PROMPT,
#         )

#         self.agent = multimodal.MultimodalAgent(
#             model=self.model,
#             chat_ctx=chat_ctx,
#             fnc_ctx=DentalAssistantFunction(),
#         )
#         self.agent.start(ctx.room, participant)

#         self.agent.on("user_started_speaking", self._on_user_started_speaking)
#         self.agent.on("user_stopped_speaking", self._on_user_stopped_speaking)

#         ctx.room.on(
#             "trackSubscribed",
#             lambda track, pub, part: asyncio.create_task(self._handle_video_track(track))
#             if track.kind == TrackKind.KIND_VIDEO
#             else None,
#         )
#         logger.info("Medical VisionAssistant started.")

#     async def _handle_video_track(self, track: Track):
#         logger.info(f"Handling video track {track.sid}")
#         video_stream = VideoStream(track)
#         last_frame_time = 0.0
#         frame_counter = 0
#         loop = asyncio.get_event_loop()

#         async for event in video_stream:
#             current_time = loop.time()
#             if current_time - last_frame_time < self._get_frame_interval():
#                 continue
#             last_frame_time = current_time
#             frame = event.frame
#             frame_counter += 1
#             logger.debug(f"Processing frame {frame_counter} from track {track.sid}")
#             try:
#                 self.model.sessions[0].push_video(frame)
#                 logger.info(f"Queued frame {frame_counter} from track {track.sid}")
#             except Exception as e:
#                 logger.error(f"Error queuing frame {frame_counter}: {e}")
#         await video_stream.aclose()

#     def _get_frame_interval(self) -> float:
#         return 1.0 / (SPEAKING_FRAME_RATE if self._is_user_speaking else NOT_SPEAKING_FRAME_RATE)

#     def _on_user_started_speaking(self):
#         self._is_user_speaking = True
#         logger.debug("User started speaking.")

#     def _on_user_stopped_speaking(self):
#         self._is_user_speaking = False
#         logger.debug("User stopped speaking.")

# async def create_sip_participant(phone_number, room_name):
#     print("Trying to call an agent")
#     livekit_api = api.LiveKitAPI(
#         os.getenv('LIVEKIT_URL'),
#         os.getenv('LIVEKIT_API_KEY'),
#         os.getenv('LIVEKIT_API_SECRET')
#     )

#     await livekit_api.sip.create_sip_participant(
#         api.CreateSIPParticipantRequest(
#             sip_trunk_id=os.getenv('SIP_TRUNK_ID'),
#             sip_call_to=phone_number,
#             room_name=room_name,
#             participant_identity=f"sip_{phone_number}",
#             participant_name="Human Agent",
#             play_ringtone=1
#         )
#     )
#     await livekit_api.aclose()

# async def main(ctx: JobContext):
#     vision_assistant = VisionAssistant()
#     await vision_assistant.start(ctx)
#     while ctx.room.connection_state == ConnectionState.CONN_CONNECTED:
#         await asyncio.sleep(1)
#     logger.info("Room disconnected; shutting down.")

# if __name__ == "__main__":
#     from livekit.agents.cli import run_app
#     run_app(WorkerOptions(entrypoint_fnc=main))

import asyncio
import logging
import os
import re
from typing import Optional, Annotated

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    llm,
    multimodal,
    cli,
    tokenize,
    tts,
)
from livekit.agents.llm import ChatContext, ChatMessage, FunctionContext
from livekit.plugins import google
from livekit.rtc import Track, TrackKind, VideoStream, ConnectionState
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
import requests

logger = logging.getLogger("vision-assistant")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(handler)

SPEAKING_FRAME_RATE = 1.0
NOT_SPEAKING_FRAME_RATE = 0.5
JPEG_QUALITY = 80

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

# Initialize RAG components
PERSIST_DIR = "./dental-knowledge-storage"
if not os.path.exists(PERSIST_DIR):
    documents = SimpleDirectoryReader("medical_data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

_SYSTEM_PROMPT = """
You are a medical assistant named "Suhita". You are designed to provide concise, accurate, and friendly answers to a wide range of queries.
Your user interacts with you via a smartphone app and may speak using their microphone or share video from their camera or screen.
When a video is shared, you may use the visual context to better understand the user's situation.
Always provide your responses in a way that is clear and supportive, avoiding jargon when possible.
"""

class DentalAssistantFunction(FunctionContext):
    @llm.ai_callable(
        description="Called when user asked a Query that can be fetched using dental knowledge base for specific information"
    )
    async def query_dental_info(
        self,
        query: Annotated[
            str,
            llm.TypeInfo(
                description="The user asked query to search in the dental knowledge base"
            )
        ],
    ):
        print(f"Answering from knowledgebase {query}")
        query_engine = index.as_query_engine(use_async=True)
        res = await query_engine.aquery(query)
        print("Query result:", res)
        return str(res)

    @llm.ai_callable(
        description="Called when asked to evaluate dental issues using vision capabilities"
    )
    async def analyze_dental_image(
        self,
        user_msg: Annotated[
            str,
            llm.TypeInfo(
                description="The user message that triggered this function"
            )
        ],
    ):
        print(f"Analyzing dental image: {user_msg}")
        # Add logic to analyze the dental image using the video frames
        return "Image analysis result"

    @llm.ai_callable(
        description="Called when a user wants to book an appointment"
    )
    async def book_appointment(
        self,
        email: Annotated[str, llm.TypeInfo(description="Email address")],
        name: Annotated[str, llm.TypeInfo(description="Patient name")],
    ):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "The email address seems incorrect. Please provide a valid one."

        try:
            webhook_url = os.getenv('WEBHOOK_URL')
            headers = {'Content-Type': 'application/json'}
            data = {'email': email, 'name': name}
            response = requests.post(webhook_url, json=data, headers=headers)
            response.raise_for_status()
            return f"Dental appointment booking link sent to {email}. Please check your email."
        except requests.RequestException as e:
            print(f"Error booking appointment: {e}")
            return "There was an error booking your dental appointment. Please try again later."

    @llm.ai_callable(
        description="Assess the urgency of a dental issue"
    )
    async def assess_dental_urgency(
        self,
        symptoms: Annotated[str, llm.TypeInfo(description="Dental symptoms")],
    ):
        urgent_keywords = ["severe pain", "swelling", "bleeding", "trauma", "knocked out", "broken"]
        if any(keyword in symptoms.lower() for keyword in urgent_keywords):
            return "call_human_agent"
        else:
            return "Your dental issue doesn't appear to be immediately urgent, but it's still important to schedule an appointment soon for a proper evaluation."

class VisionAssistant:
    def __init__(self):
        self.agent: Optional[multimodal.MultimodalAgent] = None
        self.model: Optional[google.beta.realtime.RealtimeModel] = None
        self._is_user_speaking: bool = False

    async def start(self, ctx: JobContext):
        await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        participant = await ctx.wait_for_participant()
        logger.info(f"Connected. Using participant: {participant.identity}")

        chat_ctx = llm.ChatContext(
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Your name is Suhita, a dental assistant for Knolabs Dental Agency. You are soft, caring with a bit of humour when responding. "
                        "You have access to a comprehensive dental knowledge base that includes various services, price info, and policy details, which you can reference or query to provide accurate information about dental procedures, conditions, and care. "
                        "You offer appointment booking for dental care services, including urgent attention, routine check-ups, and long-term treatments. An onsite appointment is required in most cases. "
                        "You can also analyze dental images to provide preliminary assessments, but always emphasize the need for a professional in-person examination. "
                        "Provide friendly, professional assistance and emphasize the importance of regular dental care. "
                        "Ask questions one by one and ensure you get the patient's name and email address in sequence if not already provided, encouraging the user to confirm their email to avoid any mistakes. "
                        "If the care needed is not urgent, you may ask for an image or request the user to show the dental area so you can use your vision capabilities for analysis. "
                        "Always keep your conversation engaging with multiple interactions, even when the information shared is lengthy, and try to offer an in-person appointment. "
                        "Additionally, you understand English, Hindi, and Marathi. If a user speaks or types in Hindi or Marathi, please process the input accordingly and respond in that language."
                    ),
                )
            ]
        )

        self.model = google.beta.realtime.RealtimeModel(
            voice="Puck",
            temperature=0.8,
            instructions=_SYSTEM_PROMPT,
        )

        self.agent = multimodal.MultimodalAgent(
            model=self.model,
            chat_ctx=chat_ctx,
            fnc_ctx=DentalAssistantFunction(),
        )
        self.agent.start(ctx.room, participant)

        self.agent.on("user_started_speaking", self._on_user_started_speaking)
        self.agent.on("user_stopped_speaking", self._on_user_stopped_speaking)

        ctx.room.on(
            "trackSubscribed",
            lambda track, pub, part: asyncio.create_task(self._handle_video_track(track))
            if track.kind == TrackKind.KIND_VIDEO
            else None,
        )
        logger.info("Medical VisionAssistant started.")

    async def _handle_video_track(self, track: Track):
        logger.info(f"Handling video track {track.sid}")
        video_stream = VideoStream(track)
        last_frame_time = 0.0
        frame_counter = 0
        loop = asyncio.get_event_loop()

        async for event in video_stream:
            current_time = loop.time()
            if current_time - last_frame_time < self._get_frame_interval():
                continue
            last_frame_time = current_time
            frame = event.frame
            frame_counter += 1
            logger.debug(f"Processing frame {frame_counter} from track {track.sid}")
            try:
                self.model.sessions[0].push_video(frame)
                logger.info(f"Queued frame {frame_counter} from track {track.sid}")
            except Exception as e:
                logger.error(f"Error queuing frame {frame_counter}: {e}")
        await video_stream.aclose()

    def _get_frame_interval(self) -> float:
        return 1.0 / (SPEAKING_FRAME_RATE if self._is_user_speaking else NOT_SPEAKING_FRAME_RATE)

    def _on_user_started_speaking(self):
        self._is_user_speaking = True
        logger.debug("User started speaking.")

    def _on_user_stopped_speaking(self):
        self._is_user_speaking = False
        logger.debug("User stopped speaking.")

async def create_sip_participant(phone_number, room_name):
    print("Trying to call an agent")
    livekit_api = api.LiveKitAPI(
        os.getenv('LIVEKIT_URL'),
        os.getenv('LIVEKIT_API_KEY'),
        os.getenv('LIVEKIT_API_SECRET')
    )

    await livekit_api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=os.getenv('SIP_TRUNK_ID'),
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=f"sip_{phone_number}",
            participant_name="Human Agent",
            play_ringtone=1
        )
    )
    await livekit_api.aclose()

async def main(ctx: JobContext):
    vision_assistant = VisionAssistant()
    await vision_assistant.start(ctx)
    while ctx.room.connection_state == ConnectionState.CONN_CONNECTED:
        await asyncio.sleep(1)
    logger.info("Room disconnected; shutting down.")

if __name__ == "__main__":
    from livekit.agents.cli import run_app
    run_app(WorkerOptions(entrypoint_fnc=main))
