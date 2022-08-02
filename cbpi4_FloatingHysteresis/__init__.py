# -*- coding: utf-8 -*-
import asyncio
from asyncio import tasks
import logging
from cbpi.api import *

@parameters([Property.Number(label="OffsetBefore50", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="OffsetBefore60", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="OffsetBefore70", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="OffsetAfter70", configurable=True, description="Offset below target temp when heater should switched off")])
class FloatingHysteresis(CBPiKettleLogic):
    
    async def run(self):
        try:
            self.offset_50 = float(self.props.get("OffsetBefore50", 0))
            self.offset_60 = float(self.props.get("OffsetBefore60", 0))
            self.offset_70 = float(self.props.get("OffsetBefore70", 0))
            self.offset_70plus = float(self.props.get("OffsetAfter70", 0))
            self.kettle = self.get_kettle(self.id)
            self.heater = self.kettle.heater
            logging.info("FloatingHysteresis {} {} {} {} {} {}".format(self.offset_50, self.offset_60, self.offset_70, self.offset_70plus, self.id, self.heater))       

            while self.running == True:
                sensor_value = self.get_sensor_value(self.kettle.sensor).get("value")
                target_temp = self.get_kettle_target_temp(self.id)
                if target_temp <= 50 and sensor_value >= target_temp - self.offset_50:
                    await self.actor_off(self.heater)
                elif target_temp <= 60 and sensor_value >= target_temp - self.offset_60:
                    await self.actor_off(self.heater)
                elif target_temp <= 70 and sensor_value >= target_temp - self.offset_70:
                    await self.actor_off(self.heater)
                elif sensor_value >= target_temp - self.offset_70plus:
                    await self.actor_off(self.heater)
                else:
                    await self.actor_on(self.heater)
                await asyncio.sleep(1)

        except asyncio.CancelledError as e:
            pass
        except Exception as e:
            logging.error("FloatingHysteresis Error {}".format(e))
        finally:
            self.running = False
            await self.actor_off(self.heater)



def setup(cbpi):

    '''
    This method is called by the server during startup 
    Here you need to register your plugins at the server
    
    :param cbpi: the cbpi core 
    :return: 
    '''

    cbpi.plugin.register("FloatingHysteresis", FloatingHysteresis)
