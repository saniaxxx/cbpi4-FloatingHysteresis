# -*- coding: utf-8 -*-
import asyncio
from asyncio import tasks
import logging
from cbpi.api import *

@parameters([Property.Number(label="Offset_Before_50", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Offset_Before_60", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Offset_Before_70", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Offset_After_70", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Boil_Threshold", configurable=True, default_value=98, description="When this temperature is reached, power will be set to Boil Output"),
             Property.Number(label="Boil_Output", configurable=True, default_value=50, description="Power when Boil Threshold is reached.")])
class FloatingHysteresis(CBPiKettleLogic):
    
    async def run(self):
        try:
            kettle = self.get_kettle(self.id)
            heater = kettle.heater       

            while self.running == True:
                boil_threshold = float(self.props.get("Boil_Treshold", 98))
                boil_output = int(self.props.get("Boil_Output", 50))
                offset_50 = float(self.props.get("Offset_Before_50", 0))
                offset_60 = float(self.props.get("Offset_Before_60", 0))
                offset_70 = float(self.props.get("Offset_Before_70", 0))
                offset_70plus = float(self.props.get("Offset_After_70", 0))
                current_temp = self.get_sensor_value(kettle.sensor).get("value")
                target_temp = self.get_kettle_target_temp(self.id)
                
                if current_temp >= float(boil_threshold):
                    await self.actor_on(heater, boil_output)
                elif target_temp <= 50 and current_temp >= target_temp - offset_50:
                    await self.actor_off(heater)
                elif target_temp <= 60 and current_temp >= target_temp - offset_60:
                    await self.actor_off(heater)
                elif target_temp <= 70 and current_temp >= target_temp - offset_70:
                    await self.actor_off(heater)
                elif current_temp >= target_temp - offset_70plus:
                    await self.actor_off(heater)
                else:
                    await self.actor_on(heater, 100)
                await asyncio.sleep(1)

        except asyncio.CancelledError as e:
            pass
        except Exception as e:
            logging.error("FloatingHysteresis Error {}".format(e))
        finally:
            self.running = False
            await self.actor_off(self.get_kettle(self.id).heater)

def setup(cbpi):

    '''
    This method is called by the server during startup 
    Here you need to register your plugins at the server
    
    :param cbpi: the cbpi core 
    :return: 
    '''

    cbpi.plugin.register("FloatingHysteresis", FloatingHysteresis)
